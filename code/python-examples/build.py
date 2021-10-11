import pathlib
import markdown
import typing


examples_dir = pathlib.Path("python_examples")
post_dirs = ["pydantic_powers", "github_oath_fastapi", "moto_mocks"]


def create_content_dirs(target_dir: str) -> pathlib.Path:
    target_dir = pathlib.Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def get_md_with_source(
    content_dir: pathlib.Path, posts: typing.List[str]
) -> typing.Dict[pathlib.Path, str]:
    target2source_map = {}
    for post in posts:
        md = markdown.Markdown(extensions=["mdx_include"])
        _ = md.convert((examples_dir / post / "README.md").read_text())
        target2source_map[(content_dir / f"{post}.md")] = "\n".join(md.lines)  # noqa
    return target2source_map


def write_md_with_sources(path_source_map: typing.Dict[pathlib.Path, str]) -> None:
    for path, md_source in path_source_map.items():
        path.write_text(md_source)


if __name__ == "__main__":
    content_post_dir = create_content_dirs("../../content/posts/")
    post_md_source_map = get_md_with_source(content_post_dir, post_dirs)
    write_md_with_sources(post_md_source_map)
