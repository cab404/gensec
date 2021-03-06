gensec
---
A simple scraper/autoscheduler for EteSync. Autoschedules workouts in WorldClass fitness gyms, and adds events to EteSync.

This one in particular was written for wldhx.

### configuration
See [this example](./credentials_template.yml). 

You need to specify your etesync password and cookie data.

Config is not installed in store, cause passwords.

### Installation

Regular NixOS ~~peasants~~ configuration
```nix
imports = [
    (let
        pkgs = import <nixpkgs> {};
    in
    (import (pkgs.fetchFromGitHub { # re-pin via nix-prefetch-github
        owner = "cab404";
        repo = "gensec";
        rev = "29e4d942b033c5408843d7caba6f0f1220634f00";
        sha256 = "YfwcRrEAK4EvXCf4XWK3HP38aGkRnTdlzHSoJxZNLKk=";
        fetchSubmodules = true;
    })).nixosModule.x86_64-linux)
];
services.gensec = {
    enable = true;
    config = "/home/ooof/path/to/config";
};

```

~~Glorious~~ NixOS Flakes
```nix
{
    inputs = {
        gensec.url = "github:cab404/gensec";
    };

    outputs = {self, gensec, ...}: {
        nixosConfigurations.machine = lib.nixosSystem {...}: {
            
            imports = [
                gensec.nixosModule.x86_64-linux
            ];

            services.gensec = {
                enable = true;
                config = "/home/ooof/path/to/config";
            };

        }        
        
    }
}
```