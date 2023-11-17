{ pkgs }:

pkgs.mkShell {
  name = "python";
  packages = [ pkgs.hatch ];
}
