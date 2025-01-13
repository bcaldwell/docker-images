use std::{collections::BTreeMap, env, fs};

use k8s_openapi::api::core::v1::Secret;
use kube::error::ErrorResponse;
use rand::Rng;

#[derive(Debug, serde::Deserialize)]
struct DatabaseConfig {
    username: String,
    databases: Vec<String>,
    namespace: String,
}

struct DBConnection {
    host: String,
    port: String,
    username: String,
    password: String,
}

// create connection string method on DBConnection
impl DBConnection {
    fn connection_string(&self) -> String {
        return format!(
            "host={} port={} user={} password={}",
            self.host, self.port, self.username, self.password
        );
    }
}

#[tokio::main(flavor = "current_thread")]
// #[tokio::main]
async fn main() -> anyhow::Result<()> {
    let db_connection_details = DBConnection {
        host: env::var("DB_HOST").unwrap(),
        port: env::var("DB_PORT").unwrap_or("5432".to_string()),
        username: env::var("DB_USERNAME").unwrap(),
        password: env::var("DB_PASSWORD").unwrap(),
    };

    let args: Vec<String> = env::args().collect();
    if args.len() < 1 {
        eprintln!("must pass in path to config file as first argument");
    }

    let config_filepath = std::path::Path::new(args.get(1).unwrap());
    println!("using config file: {}", config_filepath.to_str().unwrap());

    let config = fs::read_to_string(config_filepath).expect("failed to read config file");
    let db_configs: Vec<DatabaseConfig> =
        serde_json::from_str(&config).expect("failed to parse config file");

    let (client, connection) = tokio_postgres::connect(
        &db_connection_details.connection_string(),
        tokio_postgres::NoTls,
    )
    .await
    .unwrap();
    let kube_client = kube::Client::try_default().await.unwrap();

    // The connection object performs the actual communication with the database,
    // so spawn it off to run on its own.
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("connection error: {}", e);
        }
    });

    for db_config in db_configs.into_iter() {
        setup_account_for_config(&client, &kube_client, &db_connection_details, db_config).await;
    }

    Ok(())
}

async fn setup_account_for_config(
    client: &tokio_postgres::Client,
    kube_client: &kube::Client,
    db_connection_details: &DBConnection,
    db_config: DatabaseConfig,
) {
    let secrets: kube::api::Api<Secret> =
        kube::api::Api::namespaced(kube_client.clone(), &db_config.namespace);
    let secret_name = format!("{}-db-credentials", db_config.username);
    // check if secret exists in cluster
    let existing_secret = secrets.get(&secret_name).await;
    let secret_exists = match existing_secret {
        Ok(_) => {
            println!("Secret {} already exists", secret_name);
            Ok(true)
        }
        Err(e) => match e {
            kube::Error::Api(ErrorResponse { code: 404, .. }) => Ok(false),
            err => Err(err),
        },
    }
    .unwrap();

    if secret_exists {
        println!("skipping as secret already exists");
        return;
    }

    let user_password = setup_user(client, &db_config.username).await;
    for db in db_config.databases.iter() {
        setup_database(client, &db_config.username, db).await;
    }

    let mut secret_data = BTreeMap::from([
            (
                "database_host".to_string(),
                db_connection_details.host.clone(),
            ),
            (
                "database_port".to_string(),
                db_connection_details.port.clone(),
            ),
            ("username".to_string(), db_config.username.clone()),
            ("password".to_string(), user_password.clone()),
        ]);

    for (i, db) in db_config.databases.iter().enumerate() {
        secret_data.insert(format!("database.{}", i), db.clone());
        secret_data.insert(format!("database_url.{}", i), format!("host={} port={} user={} password='{}' dbname={} sslmode=disable", 
            db_connection_details.host,
            db_connection_details.port,
            db_config.username,
            user_password,
            db,
        ));
    }
    // create kubernetes secret
    let db_secret = Secret {
        metadata: k8s_openapi::apimachinery::pkg::apis::meta::v1::ObjectMeta {
            name: Some(secret_name.clone()),
            namespace: Some(db_config.namespace),
            ..Default::default()
        },
        string_data: Some(secret_data),
        ..Default::default() // data: Some(serde_json::from_value(serde_json::json!({"database": db_config.database, "username": db_config.username, "password": user_password})).unwrap()),
    };


    secrets
        .create(&kube::api::PostParams::default(), &db_secret)
        .await
        .unwrap();

    println!("successfully created secret with db creds: {}", secret_name)
}

async fn setup_user(client: &tokio_postgres::Client, username: &str) -> String {
    let user_password: String = rand::thread_rng()
        .sample_iter(rand::distributions::Alphanumeric)
        .take(20)
        .map(char::from)
        .collect();

    // check if postgres user already exists
    let user_exists = client
        .query(
            format!("SELECT 1 FROM pg_user WHERE usename='{}';", username,).as_str(),
            &[],
        )
        .await
        .unwrap();

    if user_exists.len() == 0 {
        println!("user does not exist, creating... {}", username);
        client
            .execute(
                format!(
                    "CREATE USER {} WITH PASSWORD '{}';",
                    username, user_password
                )
                .as_str(),
                &[],
            )
            .await
            .unwrap();
    } else {
        println!("user exist, updating password to match... {}", username,);
        client
            .execute(
                format!("ALTER USER {} WITH PASSWORD '{}';", username, user_password).as_str(),
                &[],
            )
            .await
            .unwrap();
    }

    return user_password;
}

async fn setup_database(client: &tokio_postgres::Client, username: &str, database: &str) {
    // check if postgres db already exists
    let db_exists = client
        .query(
            format!("SELECT 1 FROM pg_database WHERE datname='{}';", database).as_str(),
            &[],
        )
        .await
        .unwrap();

    if db_exists.len() == 0 {
        println!("database does not exist, creating... {}", database);
        client
            .execute(format!("CREATE DATABASE {}", database).as_str(), &[])
            .await
            .unwrap();
    }

    println!(
        "ensuring user {} has access to database {}",
        username, database
    );
    client
        .execute(
            format!("GRANT ALL ON DATABASE {} TO {}", database, username).as_str(),
            &[],
        )
        .await
        .unwrap();
}
