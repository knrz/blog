from os import environ
from pathlib import Path
from time import sleep
from typing import List


from notion.client import NotionClient
from notion.block import BasicBlock, CollectionViewPageBlock
from notion.operations import build_operation

from jinja2 import Template


root_dir = Path(__file__).resolve().parent.parent

with (root_dir / "templates/post.j2").open() as f:
    PostTemplate = Template(f.read())


def load_config():
    return dict(
        api_key=environ["NOTION_TOKEN"], database_url=environ["NOTION_DATABASE_URL"]
    )


def make_public(client: NotionClient, block: BasicBlock) -> bool:
    operation = build_operation(
        block.id,
        path="permissions",
        args=dict(type="public_permission", role="reader", allow_duplicate=False),
        command="setPermissionItem",
    )
    client.submit_transaction(operation)


def main():
    config = load_config()
    client = NotionClient(token_v2=config.get("api_key"))
    db = client.get_block(config.get("database_url"))
    if not isinstance(db, CollectionViewPageBlock):
        raise ValueError("NOTION_DATABASE_URL should be set to a collection page")

    filter_params = [dict(property="status", comparator="enum_is", value="Ready")]
    to_publish: List[BasicBlock] = db.collection.query(filter=filter_params)

    posts_dir = root_dir / "public/posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    for page in to_publish:
        make_public(client, page)
        url = page.get_browseable_url()
        html = PostTemplate.render(browseable_url=url)
        with (posts_dir / f"{page.id}-{page.name}.html") as f:
            f.write_text(html)


main()
