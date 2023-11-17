{

  outputs = { self, nixpkgs }: {

    devShells.aarch64-darwin.default = import ./shell.nix { pkgs = nixpkgs.legacyPackages.aarch64-darwin; };

  };
}
