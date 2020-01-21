from functools import partial
from typing import Dict, Callable, Optional

from .context import Context, ExpressionContext
from .types import Outcome, Node, FormattedLines
from .expression import format_expression
from .block import format_block


def format_func_statement(statement: Node, context: Context) -> Outcome:
    handlers = {
        "pass_stmt": partial(_format_simple_statement, "pass"),
        "func_var_stmt": _format_func_var_statement,
        "expr_stmt": _format_expr_statement,
        "return_stmt": _format_return_statement,
        "break_stmt": partial(_format_simple_statement, "break"),
        "continue_stmt": partial(_format_simple_statement, "continue"),
        "if_stmt": _format_if_statement,
        "while_stmt": partial(_format_branch, "while ", ":", 0),
        "for_stmt": _format_for_statement,
    }  # type: Dict[str, Callable]
    return handlers[statement.data](statement, context)


def _format_func_var_statement(statement: Node, context: Context) -> Outcome:
    formatted_lines = []  # type: FormattedLines
    last_processed_line_no = statement.line
    concrete_var_stmt = statement.children[0]
    if concrete_var_stmt.data == "var_assigned":
        name = concrete_var_stmt.children[0].value
        expr = concrete_var_stmt.children[1]
        expression_context = ExpressionContext(
            "var {} = ".format(name), statement.line, ""
        )
        lines, last_processed_line_no = format_expression(
            expr, expression_context, context
        )
        formatted_lines += lines
    elif concrete_var_stmt.data == "var_empty":
        name = concrete_var_stmt.children[0].value
        formatted_lines.append(
            (statement.line, "{}var {}".format(context.indent_string, name))
        )
    return (formatted_lines, last_processed_line_no)


def _format_expr_statement(statement: Node, context: Context) -> Outcome:
    expr = statement.children[0]
    expression_context = ExpressionContext("", statement.line, "")
    return format_expression(expr, expression_context, context)


def _format_return_statement(statement: Node, context: Context) -> Outcome:
    if len(statement.children) == 0:
        return _format_simple_statement("return", statement, context)
    expr = statement.children[0]
    expression_context = ExpressionContext("return ", statement.line, "")
    return format_expression(expr, expression_context, context)


def _format_simple_statement(
    statement_name: str, statement: Node, context: Context
) -> Outcome:
    return (
        [(statement.line, "{}{}".format(context.indent_string, statement_name))],
        statement.line,
    )


def _format_if_statement(statement: Node, context: Context) -> Outcome:
    formatted_lines = []  # type: FormattedLines
    for branch in statement.children:
        branch_prefix = {
            "if_branch": "if ",
            "elif_branch": "elif ",
            "else_branch": "else",
        }[branch.data]
        expr_position = {"if_branch": 0, "elif_branch": 0, "else_branch": None}[
            branch.data
        ]
        lines, last_processed_line_no = _format_branch(
            branch_prefix, ":", expr_position, branch, context
        )
        formatted_lines += lines
    return (formatted_lines, last_processed_line_no)


def _format_for_statement(statement: Node, context: Context) -> Outcome:
    prefix = "for {} in ".format(statement.children[0].value)
    suffix = ":"
    expr_position = 1
    return _format_branch(prefix, suffix, expr_position, statement, context)


def _format_branch(
    prefix: str,
    suffix: str,
    expr_position: Optional[int],
    statement: Node,
    context: Context,
) -> Outcome:
    if expr_position is not None:
        expr = statement.children[expr_position]
        expression_context = ExpressionContext(prefix, statement.line, suffix)
        header_lines, last_processed_line_no = format_expression(
            expr, expression_context, context
        )
        offset = expr_position + 1
    else:
        header_lines = [
            (statement.line, "{}{}{}".format(context.indent_string, prefix, suffix))
        ]
        last_processed_line_no = statement.line
        offset = 0
    body_lines, last_processed_line_no = format_block(
        statement.children[offset:],
        format_func_statement,
        context.create_child_context(last_processed_line_no),
    )
    return (header_lines + body_lines, last_processed_line_no)