"""Turntable GIF of a point cloud.

Open3D renders in a hidden window. If that fails (no OpenGL, remote desktop),
falls back to matplotlib 3D scatter plots.
"""
import copy

import numpy as np
from PIL import Image

BG = (0.1, 0.1, 0.1)  # dark background, same as view.py


# --- Open3D offscreen frames ---

def frames_open3d(pcd, n_frames=36, size=(640, 480), point_size=2.5, tilt_deg=15, zoom=0.6):
    import open3d as o3d
    vis = o3d.visualization.Visualizer()
    if not vis.create_window(width=size[0], height=size[1], visible=False):
        raise RuntimeError("Open3D could not open an offscreen window")
    pcd = copy.deepcopy(pcd)  # we rotate it; leave the caller's cloud alone
    center = np.median(np.asarray(pcd.points), axis=0)
    vis.add_geometry(pcd)
    opt = vis.get_render_option()
    opt.point_size = point_size
    opt.background_color = np.array(BG)

    # camera: looking at the center from the front (+z), slightly above
    t = np.radians(tilt_deg)
    ctr = vis.get_view_control()
    ctr.set_lookat(center)
    ctr.set_up([0, 1, 0])
    ctr.set_front([0, np.sin(t), np.cos(t)])  # Open3D "front" points from the target to the camera
    ctr.set_zoom(zoom)

    # spin the cloud about the vertical (y) axis instead of moving the camera
    step = o3d.geometry.get_rotation_matrix_from_axis_angle([0, 2 * np.pi / n_frames, 0])
    frames = []
    for _ in range(n_frames):
        vis.update_geometry(pcd)
        vis.poll_events()
        vis.update_renderer()
        img = np.asarray(vis.capture_screen_float_buffer(do_render=True))
        frames.append(Image.fromarray((img * 255).astype(np.uint8)))
        pcd.rotate(step, center=center)
    vis.destroy_window()
    return frames


# --- matplotlib fallback frames ---

def frames_matplotlib(pcd, n_frames=36, size=(640, 480), tilt_deg=15, max_points=20000):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xyz = np.asarray(pcd.points)
    rgb = np.asarray(pcd.colors)
    if len(xyz) > max_points:  # scatter gets slow with many points
        idx = np.random.default_rng(0).choice(len(xyz), max_points, replace=False)
        xyz, rgb = xyz[idx], rgb[idx]
    # matplotlib's vertical axis is z; ours is y. Plot (x, -z, y) so azim=-90 is the front view.
    X, Y, Z = xyz[:, 0], -xyz[:, 2], xyz[:, 1]

    fig = plt.figure(figsize=(size[0] / 100, size[1] / 100), dpi=100, facecolor=BG)
    ax = fig.add_subplot(projection="3d", facecolor=BG)
    ax.scatter(X, Y, Z, c=rgb, s=1, depthshade=False)
    ax.set_box_aspect((np.ptp(X), np.ptp(Y), np.ptp(Z)))  # equal scale on all axes
    ax.set_axis_off()
    frames = []
    for i in range(n_frames):
        ax.view_init(elev=tilt_deg, azim=-90 + 360 * i / n_frames)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()))
    plt.close(fig)
    return frames


# --- GIF ---

def save_turntable(pcd, gif_path, fps=12, force_matplotlib=False):
    """Write a 360-degree turntable GIF. Returns the renderer used ('open3d' or 'matplotlib')."""
    method = "matplotlib"
    frames = None
    if not force_matplotlib:
        try:
            frames = frames_open3d(pcd)
            method = "open3d"
        except Exception as e:
            print(f"Open3D offscreen rendering failed ({e}); using matplotlib fallback")
    if frames is None:
        frames = frames_matplotlib(pcd)
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps), loop=0)
    return method
