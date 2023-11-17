{ pkgs }:

let
  pythonEnv = pkgs.python310.withPackages (ps: with ps; [
    hatch
  ]);

in pkgs.mkShell {
  name = "python";
  packages = [ pkgs.hatch ];
}
