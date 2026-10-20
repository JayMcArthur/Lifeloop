{
  description = "LifeLoop solver: locked Python and C++ toolchain";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/78e9c786dc08cd4f3420c2395cd977206a9b1da2";
  outputs = { nixpkgs, ... }: let
    pkgs = import nixpkgs { system = "x86_64-linux"; };
  in {
    devShells.x86_64-linux.default = pkgs.mkShellNoCC {
      packages = [ pkgs.python313 pkgs.gcc pkgs.util-linux pkgs.coreutils pkgs.systemd ];
      PYTHONDONTWRITEBYTECODE = "1";
    };
  };
}
