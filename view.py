"""Open a .ply point cloud in the Open3D viewer.

    python view.py results/sample/sparse.ply

Controls: left-drag rotate, scroll zoom, ctrl+left-drag pan, +/- point size, Q or Esc close.
"""
import argparse
from pathlib import Path

import open3d as o3d


def main():
    parser = argparse.ArgumentParser(description="View a .ply point cloud.")
    parser.add_argument("ply", help="path to .ply file")
    parser.add_argument("--point-size", type=float, default=3.0)
    args = parser.parse_args()

    if not Path(args.ply).is_file():
        raise SystemExit(f"ERROR: file not found: {args.ply}")
    pcd = o3d.io.read_point_cloud(args.ply)
    if pcd.is_empty():
        raise SystemExit(f"ERROR: no points in {args.ply}")
    print(f"{len(pcd.points)} points. Close the window (Q) to exit.")

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name=Path(args.ply).name, width=1280, height=800)
    vis.add_geometry(pcd)
    opt = vis.get_render_option()
    opt.point_size = args.point_size   # sparse clouds look empty at the default 1 px
    opt.background_color = [0.1, 0.1, 0.1]
    vis.run()
    vis.destroy_window()


if __name__ == "__main__":
    main()
