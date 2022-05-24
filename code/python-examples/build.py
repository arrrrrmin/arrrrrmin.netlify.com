import pathlib
import markdown
import typing


examples_dir = pathlib.Path("python_examples")
post_dirs: typing.List[str] = [
    "albert_pretraining",
    "pydantic_powers",
    "github_oath_fastapi",
    "moto_mocks",
    "oauth_at_cloudfront",
    "sign_cf_cookies",
]


def get_md_with_source(
    content_dir: pathlib.Path
) -> typing.Dict[pathlib.Path, str]:
    target2source_map = {}
    for post in post_dirs:
        md = markdown.Markdown(extensions=["mdx_include"])
        _ = md.convert((examples_dir / post / "README.md").read_text())
        target2source_map[(content_dir / f"{post}.md")] = "\n".join(md.lines)  # noqa
    return target2source_map


def write_md_with_sources(path_source_map: typing.Dict[pathlib.Path, str]) -> None:
    for path, md_source in path_source_map.items():
        print(f"Writing source to {path}")
        path.write_text(md_source)


if __name__ == "__main__":
    content_post_dir = pathlib.Path("../../content/posts/")
    content_post_dir.mkdir(parents=True, exist_ok=True)
    post_md_source_map = get_md_with_source(content_post_dir)
    write_md_with_sources(post_md_source_map)
