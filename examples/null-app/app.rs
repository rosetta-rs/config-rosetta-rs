fn main() {
    let config = Config::load();
    println!("{:?}", config);
}

#[derive(Clone, Default, Debug)]
struct Config {
    host: Option<String>,
    port: Option<u16>,
    debug: Option<bool>,
}

impl Config {
    fn load() -> Self {
        const NAME: &str = "example.toml";

        let mut merged = Self::from_defaults();

        if let Some(dirs) = directories::ProjectDirs::from("", "", "example") {
            let config_root = dirs.config_dir();
            if let Some(layer) = std::fs::read_to_string(config_root.join(NAME))
                .ok()
                .and_then(|s| toml::from_str(&s).ok())
            {
                let layer = Self::from_toml(&layer);
                merged.update(layer);
            }
        }

        let cwd = std::env::current_dir();
        for config_root in cwd
            .as_deref()
            .map(|c| c.ancestors())
            .ok()
            .into_iter()
            .flatten()
        {
            if let Some(layer) = std::fs::read_to_string(config_root.join(NAME))
                .ok()
                .and_then(|s| toml::from_str(&s).ok())
            {
                let layer = Self::from_toml(&layer);
                merged.update(layer);
                break;
            }
        }

        merged.update(Self::from_env());

        merged
    }

    fn new() -> Self {
        Self::default()
    }

    fn from_toml(toml: &toml::Value) -> Self {
        Self {
            host: toml
                .get("host")
                .and_then(|v| v.as_str())
                .map(|s| s.to_owned()),
            port: toml
                .get("port")
                .and_then(|v| v.as_integer())
                .and_then(|i| i.try_into().ok()),
            debug: toml.get("debug").and_then(|v| v.as_bool()),
        }
    }

    fn from_env() -> Self {
        Self {
            host: std::env::var_os("APP_HOST").and_then(|s| s.to_str().map(|s| s.to_owned())),
            port: std::env::var_os("APP_PORT")
                .and_then(|s| s.to_str().map(|s| s.to_owned()))
                .and_then(|s| s.parse().ok()),
            debug: std::env::var_os("APP_DEBUG")
                .and_then(|s| s.to_str().map(|s| s.to_owned()))
                .and_then(|s| s.parse().ok()),
        }
    }

    fn from_defaults() -> Self {
        let empty = Self::new();
        Self {
            host: Some(empty.host().to_owned()),
            port: Some(empty.port()),
            debug: Some(empty.debug()),
        }
    }
}

impl Config {
    fn update(&mut self, other: Config) {
        if let Some(other) = other.host {
            self.host = Some(other);
        }
        if let Some(other) = other.port {
            self.port = Some(other);
        }
        if let Some(other) = other.debug {
            self.debug = Some(other);
        }
    }

    fn host(&self) -> &str {
        self.host.as_deref().unwrap_or("localhost")
    }

    fn port(&self) -> u16 {
        self.port.unwrap_or(3000)
    }

    fn debug(&self) -> bool {
        self.debug.unwrap_or(false)
    }
}
