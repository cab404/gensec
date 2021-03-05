{
    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    };

    outputs = {self, nixpkgs}:
    let pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in {

        devShell.x86_64-linux = pkgs.mkShell {
            buildInputs = with pkgs; [
                python3Packages.poetry
                geckodriver
            ];
        };

        defaultPackage.x86_64-linux = with pkgs.poetry2nix; mkPoetryApplication {
            projectDir = ./.;
            preferWheels = true;
        };

        nixosModule.x86_64-linux = { config }: with nixpkgs.lib; {
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
                        ExecStart = "${self.defaultPackages.x86_64-linux}/bin/gensec";
                    };
                    environment = {
                        GENSEC_CONFIG = config.services.gensec.config;
                    };
                };

                systemd.timers.home-locatedb = {
                    partOf = "gensec.service";
                    timerConfig = {
                        OnCalendar = "*-*-* 00:00";
                    };
                    wantedBy = [ "timers.target" ];
                };

            };
        };

    };

}