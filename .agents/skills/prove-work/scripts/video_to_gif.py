#!/usr/bin/env python3
"""Convert a Playwright .webm recording to an optimized GIF and optionally upload to GitHub.

Pipeline: webm -> pyav decode -> Pillow quantize -> GIF save -> gifsicle optimize -> gh upload
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

OUTPUT_DIR = Path("/tmp/prove-work")


def ensure_dependencies():
    """Install required pip packages if missing."""
    missing = []
    try:
        import av  # noqa: F401
    except ImportError:
        missing.append("av")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        missing.append("pillow")

    if missing:
        print(f"Installing: {', '.join(missing)}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )


def check_gifsicle():
    """Check if gifsicle is available. Return True if found."""
    return shutil.which("gifsicle") is not None


def decode_webm(webm_path, target_fps=10, max_width=800):
    """Decode a .webm file into a list of PIL Images at the target fps and resolution."""
    import av
    from PIL import Image

    container = av.open(str(webm_path))
    stream = container.streams.video[0]
    src_fps = float(stream.average_rate) if stream.average_rate else 30.0
    frame_skip = max(1, round(src_fps / target_fps))

    frames = []
    for i, frame in enumerate(container.decode(video=0)):
        if i % frame_skip != 0:
            continue
        img = frame.to_image()
        if img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.LANCZOS)
        frames.append(img)

    container.close()
    return frames


def save_gif(frames, output_path, fps=10, colors=128):
    """Save a list of PIL Images as an animated GIF."""
    from PIL import Image

    duration_ms = int(1000 / fps)
    quantized = [f.quantize(colors=colors, method=Image.Quantize.MEDIANCUT) for f in frames]

    quantized[0].save(
        str(output_path),
        save_all=True,
        append_images=quantized[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )


def optimize_gif(input_path, output_path, lossy=80, colors=128):
    """Optimize a GIF using gifsicle. Returns output file size in bytes."""
    subprocess.run(
        [
            "gifsicle",
            "-O3",
            f"--lossy={lossy}",
            "--colors", str(colors),
            "-o", str(output_path),
            str(input_path),
        ],
        check=True,
        capture_output=True,
    )
    return Path(output_path).stat().st_size


def enforce_size_limit(webm_path, output_path, max_size_bytes):
    """Convert webm to GIF, progressively reducing quality until under the size limit.

    Reduction strategy:
    1. Default: 10fps, 800px, 128 colors
    2. Reduce colors to 64
    3. Reduce fps to 8
    4. Reduce width to 640
    5. Truncate to first 10 seconds of frames
    6. Fail with error
    """
    has_gifsicle = check_gifsicle()
    raw_path = output_path.with_suffix(".raw.gif")

    strategies = [
        {"fps": 10, "max_width": 800, "colors": 128, "truncate": None},
        {"fps": 10, "max_width": 800, "colors": 64, "truncate": None},
        {"fps": 8, "max_width": 800, "colors": 64, "truncate": None},
        {"fps": 8, "max_width": 640, "colors": 64, "truncate": None},
        {"fps": 8, "max_width": 640, "colors": 64, "truncate": 80},  # ~10s at 8fps
    ]

    for i, s in enumerate(strategies):
        label = f"attempt {i + 1}/{len(strategies)}: {s['fps']}fps, {s['max_width']}px, {s['colors']} colors"
        if s["truncate"]:
            label += f", truncated to {s['truncate']} frames"
        print(f"  {label}...")

        frames = decode_webm(webm_path, target_fps=s["fps"], max_width=s["max_width"])
        if not frames:
            print("ERROR: No frames extracted from video.", file=sys.stderr)
            sys.exit(1)

        if s["truncate"] and len(frames) > s["truncate"]:
            frames = frames[: s["truncate"]]

        save_gif(frames, raw_path, fps=s["fps"], colors=s["colors"])

        if has_gifsicle:
            size = optimize_gif(raw_path, output_path, lossy=80, colors=s["colors"])
            raw_path.unlink(missing_ok=True)
        else:
            shutil.move(str(raw_path), str(output_path))
            size = output_path.stat().st_size

        size_mb = size / (1024 * 1024)
        print(f"  -> {size_mb:.1f} MB")

        if size <= max_size_bytes:
            print(f"GIF saved: {output_path} ({size_mb:.1f} MB)")
            return

    raw_path.unlink(missing_ok=True)
    print(
        f"ERROR: Could not reduce GIF below {max_size_bytes / (1024 * 1024):.0f} MB after all strategies.",
        file=sys.stderr,
    )
    print(f"Last attempt: {output_path} ({size_mb:.1f} MB)", file=sys.stderr)
    sys.exit(1)


def upload_to_github(gif_path, repo, pr_number=None):
    """Upload GIF to a media-assets GitHub release and return the download URL.

    Creates the release if it doesn't exist. Embeds the URL in the PR body if pr_number is given.
    """
    # Ensure media-assets release exists
    result = subprocess.run(
        ["gh", "release", "view", "media-assets", "--repo", repo],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Creating media-assets release...")
        subprocess.run(
            [
                "gh", "release", "create", "media-assets",
                "--repo", repo,
                "--title", "Media Assets",
                "--notes", "GIF artifacts for PRs. Auto-managed by prove-work skill.",
                "--latest=false",
            ],
            check=True,
            capture_output=True,
        )

    # Generate unique asset name
    ts = time.strftime("%Y%m%d-%H%M%S")
    stem = f"demo-pr{pr_number}-{ts}" if pr_number else f"demo-{ts}"
    asset_name = f"{stem}.gif"

    # Copy with the asset name
    asset_path = gif_path.parent / asset_name
    shutil.copy2(str(gif_path), str(asset_path))

    # Upload
    print(f"Uploading {asset_name} to media-assets release...")
    subprocess.run(
        [
            "gh", "release", "upload", "media-assets",
            str(asset_path),
            "--repo", repo,
            "--clobber",
        ],
        check=True,
    )

    # Get download URL
    result = subprocess.run(
        [
            "gh", "release", "view", "media-assets",
            "--repo", repo,
            "--json", "assets",
            "--jq", f'.assets[] | select(.name=="{asset_name}") | .url',
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    url = result.stdout.strip()

    if not url:
        # Fallback: construct URL from repo
        url = f"https://github.com/{repo}/releases/download/media-assets/{asset_name}"

    print(f"Uploaded: {url}")
    asset_path.unlink(missing_ok=True)

    # Embed in PR if specified
    if pr_number:
        embed_in_pr(repo, pr_number, url)

    return url


def embed_in_pr(repo, pr_number, gif_url):
    """Upsert a ## Demo section in the PR body with the GIF embedded."""
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "body", "--jq", ".body"],
        capture_output=True,
        text=True,
        check=True,
    )
    body = result.stdout.strip()

    demo_section = f"\n\n## Demo\n\n![Demo]({gif_url})\n"

    # Replace existing ## Demo section or append
    import re
    demo_pattern = r"\n*## Demo\n.*?(?=\n## |\Z)"
    if re.search(demo_pattern, body, re.DOTALL):
        new_body = re.sub(demo_pattern, demo_section, body, flags=re.DOTALL)
    else:
        new_body = body + demo_section

    subprocess.run(
        ["gh", "pr", "edit", str(pr_number), "--repo", repo, "--body", new_body],
        check=True,
    )
    print(f"Embedded GIF in PR #{pr_number} ## Demo section.")


def find_webm(input_path):
    """Resolve input to a single .webm file path."""
    p = Path(input_path)
    if p.is_file() and p.suffix == ".webm":
        return p

    # If it's a directory, find the most recent .webm
    if p.is_dir():
        webms = sorted(p.glob("*.webm"), key=lambda f: f.stat().st_mtime, reverse=True)
        if webms:
            return webms[0]

    # Try glob pattern
    matches = sorted(glob.glob(input_path), key=lambda f: os.path.getmtime(f), reverse=True)
    webms = [Path(m) for m in matches if m.endswith(".webm")]
    if webms:
        return webms[0]

    return None


def main():
    parser = argparse.ArgumentParser(description="Convert Playwright .webm to optimized GIF")
    parser.add_argument("--input", "-i", required=True, help="Path to .webm file or directory containing .webm files")
    parser.add_argument("--output", "-o", default=None, help="Output .gif path (default: /tmp/prove-work/demo.gif)")
    parser.add_argument("--max-size-mb", type=float, default=10.0, help="Maximum GIF size in MB (default: 10)")
    parser.add_argument("--fps", type=int, default=10, help="Target frame rate (default: 10)")
    parser.add_argument("--max-width", type=int, default=800, help="Max width in pixels (default: 800)")
    parser.add_argument("--colors", type=int, default=128, help="Color palette size (default: 128)")
    parser.add_argument("--upload", action="store_true", help="Upload to GitHub release")
    parser.add_argument("--repo", default=None, help="GitHub repo (owner/name) for upload")
    parser.add_argument("--pr", type=int, default=None, help="PR number to embed GIF into")

    args = parser.parse_args()

    # Ensure deps
    ensure_dependencies()

    # Check gifsicle
    if not check_gifsicle():
        print("WARNING: gifsicle not found. GIF optimization will be skipped.", file=sys.stderr)
        print("Install with: brew install gifsicle", file=sys.stderr)

    # Find input
    webm_path = find_webm(args.input)
    if not webm_path:
        print(f"ERROR: No .webm file found at: {args.input}", file=sys.stderr)
        sys.exit(1)
    print(f"Input: {webm_path}")

    # Set output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else OUTPUT_DIR / "demo.gif"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert
    max_size_bytes = int(args.max_size_mb * 1024 * 1024)
    print(f"Converting to GIF (max {args.max_size_mb} MB)...")
    enforce_size_limit(webm_path, output_path, max_size_bytes)

    # Upload
    if args.upload:
        if not args.repo:
            # Auto-detect repo from git remote
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                args.repo = result.stdout.strip()
            else:
                print("ERROR: Could not detect repo. Provide --repo owner/name.", file=sys.stderr)
                sys.exit(1)

        url = upload_to_github(output_path, args.repo, args.pr)
        print(f"\nGIF URL: {url}")
    else:
        print(f"\nGIF saved to: {output_path}")
        if args.pr:
            print("Note: Use --upload to upload and embed in the PR.")


if __name__ == "__main__":
    main()
