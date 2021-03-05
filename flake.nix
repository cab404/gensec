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

    };

}