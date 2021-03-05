{
    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
        utils.url = "github:numtide/flake-utils";
    };

    outputs = {self, nixpkgs, utils}:
    let out = system:
    let pkgs = nixpkgs.legacyPackages."${system}";
    in {

        devShell = pkgs.mkShell {
            buildInputs = with pkgs; [
                python3Packages.poetry
                geckodriver
            ];
        };

        defaultPackage = with pkgs.poetry2nix; mkPoetryApplication {
            projectDir = ./.;
            preferWheels = true;
        };

        defaultApp = utils.lib.mkApp {
            drv = self.defaultPackage."${system}";
        };

        nixosModule = { config, ... }: with nixpkgs.lib; {
            options = {
                services.gensec = {
                    enable = mkEnableOption "enables gensec service, yup.";
                    config = mkOption {
                        type = types.path;
                        default = null;
                        description = ''
                            Path to secret gensec config.
                        '';
                    };
                };
            };
            config = mkIf config.services.gensec.enable {
                systemd.services.gensec = {
                    serviceConfig = {
                        ExecStart = "${self.defaultPackage."${system}"}/bin/gensec";
                    };
                    environment = {
                        GENSEC_CONFIG = config.services.gensec.config;
                    };
                };

                systemd.timers.gensec = {
                    partOf = [ "gensec.service" ];
                    timerConfig = {
                        OnCalendar = "*-*-* 00:00";
                    };
                    wantedBy = [ "timers.target" ];
                };

            };
        };

    }; in with utils.lib; eachSystem defaultSystems out;

}