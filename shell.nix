{ pkgs }:

let
  pythonEnv = pkgs.python310.withPackages (ps: with ps; [
    pytest
  ]);

in pkgs.mkShell {
  name = "python";
  packages = [ pythonEnv ];
}
