from pathlib import Path
import ast


class MethodCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.methods: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.methods.add(item.name)

        self.generic_visit(node)


def get_method_names() -> set[str]:
    methods = set()
    for path in Path('hydrogram/methods').rglob('*.py'):
        if path.name == '__init__.py':
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'))
        collector = MethodCollector()
        collector.visit(tree)
        methods.update(collector.methods)

    return methods


def test_issue_50_compat_methods_are_implemented():
    methods = get_method_names()

    expected = {
        'forward_message',
        'copy_messages',
        'delete_message',
        'get_chat_member_count',
        'set_chat_administrator_custom_title',
        'set_user_emoji_status',
        'set_my_commands',
        'get_my_commands',
        'delete_my_commands',
        'get_chat_administrators',
        'close_general_forum_topic',
        'edit_general_forum_topic',
        'reopen_general_forum_topic',
        'hide_general_forum_topic',
        'unhide_general_forum_topic',
        'unpin_all_forum_topic_messages',
        'unpin_all_general_forum_topic_messages',
        'set_message_reaction',
        'close',
    }

    missing = expected - methods
    assert not missing
