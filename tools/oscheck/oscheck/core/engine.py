#!/usr/bin/python3
#
# Copyright (c) 2025, Oracle and/or its affiliates.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
#
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 only, as
# published by the Free Software Foundation.
#
# This code is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# version 2 for more details (a copy is included in the LICENSE file that
# accompanied this code).
#
# You should have received a copy of the GNU General Public License version
# 2 along with this work; if not, see <https://www.gnu.org/licenses/>.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.
#
# Authors:
#   Ryan McCabe <ryan.m.mccabe@oracle.com>

"""OHC rule engine core logic"""

import os
import ast
import operator
import re
import base64
import logging

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from oscheck.core.util import get_file_contents, compare_file_contents, \
                              compute_hash_from_str

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")

global_vars = {}

__all__ = ["global_vars", "validate_rule",
           "compare", "get_required_attributes"]


VALID_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def rule_implies_nonexistence(rule: Any) -> bool:
    """Returns true if a rule is checking for nonexistence"""
    if rule == {"exists": False}:
        return True
    if isinstance(rule, dict) and "not" in rule:
        inner = rule["not"]
        if inner == {"exists": True}:
            return True
    return False


def get_required_attributes(rule: Any) -> List[str]:
    """
    Walk a rule file and determine which attributes
    are required to evaluate the rule, so that we can
    avoid loading data we won't need. Returns a list
    of required attributes.
    """
    required = set()

    def walk(r):
        if isinstance(r, dict):
            for k, v in r.items():
                if k in {"and", "or"}:
                    for item in v:
                        walk(item)
                elif k == "not":
                    walk(v)
                else:
                    required.add(k)
                    walk(v)
        elif isinstance(r, list):
            for item in r:
                walk(item)

    walk(rule)
    return list(required)


def eval_expr(expr: str, value: Any = None) -> float:
    """
    Safely evaluate an expression
    Replacement done on tokens:
      $value = left side value
      $xyz: global_vars.get(xyz, "")
    """
    INTERNAL.debug(f"Evaluating expression: {expr}")
    local_vars = {"value": value}

    def replace_var(match):
        name = match.group(1)
        INTERNAL.debug(f"Replacing ${name} in expr")
        ret = str(global_vars.get(name, ""))
        if not ret:
            ret = str(local_vars.get(name, ""))
        return ret

    expr = re.sub(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", replace_var, expr)
    INTERNAL.debug(f"Expr after sub: {expr}")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax for {expr}: {e}")

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        elif isinstance(node, ast.Num):
            # For Python 3.6, since no ast.Constant
            return node.n
        elif isinstance(node, ast.BinOp):
            return VALID_OPS[type(node.op)](
                eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return VALID_OPS[type(node.op)](eval_node(node.operand))
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")

    return eval_node(tree)


def compare_identical(value: Any,
                      expected: Dict[str, Any],
                      attribute: str,
                      context: str,
                      fatal_err: Optional[List[str]] = None) -> bool:
    """Compare @value (left side, file contents, @value) vs @expected["value"]
     - [@expected["type"]="file"]   Another file's contents.
     - [@expected["type"]="sha256"] The SHA256 hash of the file specified
     - [@expected["type"]="base64"] The contents of a decoded base64 string
     - [@expected["type"]="string"] A string
    """
    INTERNAL.debug(
        f"Compare_identical called for"
        f" {attribute} in {context} for {value} vs {expected}")

    if not isinstance(expected, dict) \
       or "type" not in expected \
       or "value" not in expected:
        err_str = f"{context}: {attribute} : Expected dict, got {expected}"
        EXTERNAL.debug("%s", err_str)
        if fatal_err:
            fatal_err.append(err_str)
        return False

    ident_type = expected["type"].lower()
    ident_val = expected["value"]

    if not isinstance(value, (bytes, str)):
        err_str = f"{context}: {attribute} - " \
            f"Expected string or bytes, got {type(value).__name__}: {value}"
        EXTERNAL.debug("%s", err_str)
        if fatal_err:
            fatal_err.append(err_str)
        return False

    if ident_type == "file":
        if not os.path.exists(ident_val):
            err_str = f"{context}: {attribute} - " \
                f"Reference file '{ident_val}' does not exist."
            if fatal_err is not None:
                fatal_err.append(err_str)
            EXTERNAL.debug("%s", err_str)
            return False

        err_str = ""
        try:
            rfile_contents = get_file_contents(ident_val)
        except Exception as e:
            rfile_contents = None
            err_str = e

        if rfile_contents is None:
            err_str = f"{context}: {attribute} - " \
                f"Failed to read file '{ident_val}': {err_str}."
            if fatal_err is not None:
                fatal_err.append(err_str)
            EXTERNAL.debug("%s", err_str)
            return False

        if compare_file_contents(value, rfile_contents):
            INTERNAL.debug(
                f"OK: {context}: {attribute} "
                f"matches file '{ident_val}'.")
            return True
        else:
            INTERNAL.debug(
                f"ERROR: {context}: {attribute} - File content mismatch.\n"
                f"  Expected:\n{rfile_contents}\n"
                f"  Got:\n{value}\n"
            )
            return False
    elif ident_type == "base64":
        INTERNAL.debug(f"GETTING base64 DECODED CONTENTS OF {context}")
        try:
            decoded_content = base64.b64decode(ident_val).decode()

            if compare_file_contents(decoded_content, value):
                INTERNAL.debug(
                    f"OK: {context}: {attribute} "
                    "matches base64-decoded content.")
                return True
            else:
                INTERNAL.debug("ERROR"
                               f" {context}: {attribute}"
                               "- Base64 content mismatch.\n"
                               f"  Expected (decoded):\n{decoded_content}\n"
                               f"  Got (value):\n{value}\n")
                return False
        except Exception as e:
            err_str = f"{context}: {attribute} - " \
                f"Error decoding base64 string: {e}"
            if fatal_err is not None:
                fatal_err.append(err_str)
            EXTERNAL.debug("%s", err_str)
            return False
    elif ident_type == "sha256":
        computed_hash = compute_hash_from_str(value)
        if computed_hash is None:
            err_str = f"Unable to get sha256sum for {context}"
            if fatal_err is not None:
                fatal_err.append(err_str)
            EXTERNAL.debug("%s", err_str)
            return False

        if computed_hash != ident_val:
            INTERNAL.debug(
                f"ERROR: {context}: {attribute} - SHA256 hash mismatch."
                f"Expected: {ident_val}, Got: {computed_hash}")
            return False
        else:
            INTERNAL.debug(
                f"OK: {context}: computed sha256 {computed_hash}"
                f"matches provided {ident_val}")
        return True
    elif ident_type == "string":
        if compare_file_contents(value, ident_val):
            INTERNAL.debug(
                f"OK: {context}: {attribute} matches expected string.")
            return True
        else:
            INTERNAL.debug(
                f"ERROR: {context}: {attribute} - String content mismatch."
                f"Expected: '{ident_val}', Got: '{value}'.")
            return False

    err_str = f"{context}: {attribute} - " \
              f"Invalid identical type: {ident_type}"
    if fatal_err is not None:
        fatal_err.append(err_str)
    EXTERNAL.debug("%s", err_str)
    return False


def compare(val: Any,
            rule: Union[Dict[str, Any], Any],
            attr: str,
            context: str,
            fatal_err: Optional[List[str]] = None,
            plugin_ops: Optional[Dict[str, Callable]] = None) -> bool:
    """Compares @val based on the provided @rule and defined
    comparitors.
    """

    success = True

    if not isinstance(rule, dict):
        # A comparison on an object that's not a dict is
        # an implicit equals rule.
        rule = {"eq": rule}

    for op, expected in rule.items():
        op = op.lower()

        try:
            if isinstance(expected, dict) and "expr" in expected:
                try:
                    expected = eval_expr(expected["expr"], val)
                    INTERNAL.debug(f"Expr evaluated to {expected}")
                except Exception as e:
                    err_str = \
                        f"{context}: {attr} - Error evaluating expression: {e}"
                    if fatal_err is not None:
                        fatal_err.append(err_str)
                    EXTERNAL.debug("%s - global vars=%s", err_str, global_vars)
                    return False

            if plugin_ops and op in plugin_ops:
                INTERNAL.debug(f"Using op {op} from plugin-specific ops")
                try:
                    result = plugin_ops[op](val, expected)
                    if result:
                        INTERNAL.debug(
                            f"OK: {context}: {attr} passed plugin '{op}' "
                            f"check (expected={expected}, value={val})")
                    else:
                        INTERNAL.debug(
                            f"ERROR: {context}: {attr} failed plugin '{op}' "
                            f"check (expected={expected}, got={val})")
                        success = False
                    continue
                except Exception as e:
                    err_str = \
                        f"{context}: {attr}: Error in plugin op {op}: {e}"
                    if fatal_err:
                        fatal_err.append(err_str)
                    EXTERNAL.debug("%s", err_str)
                    return False

            if op == "identical":
                result = compare_identical(val, expected, attr,
                                           context, fatal_err=fatal_err)
                if not result:
                    success = False
                continue

            # Convert numerical values from strings if necessary
            if isinstance(val, str) and isinstance(expected, (int, float)):
                val = float(val) if '.' in val else int(val)

            result = False

            if op == "eq":
                result = val == expected
            elif op == "ne":
                result = val != expected
            elif op == "gt":
                result = isinstance(val, (int, float)) \
                    and isinstance(expected, (int, float)) \
                    and val > expected
            elif op == "ge":
                result = isinstance(val, (int, float)) \
                    and isinstance(expected, (int, float)) \
                    and val >= expected
            elif op == "lt":
                result = isinstance(val, (int, float)) \
                    and isinstance(expected, (int, float)) \
                    and val < expected
            elif op == "le":
                result = isinstance(val, (int, float)) \
                    and isinstance(expected, (int, float)) \
                    and val <= expected
            elif op == "bitwise_and":
                result = isinstance(val, int) \
                    and (val & expected) == expected
            elif op == "exists":
                result = (val is not None) == expected
            elif op == "contains":
                result = isinstance(val, (str, list, tuple, set)) \
                    and expected in val
            elif op == "regex":
                INTERNAL.debug(
                    f"REGEX Looking for pattern {expected} in {str(val)}")
                result = val is not None \
                    and isinstance(expected, str) \
                    and bool(re.search(expected, str(val), re.MULTILINE))
            else:
                err_str = f"{context}: {attr} - " \
                    f"Unknown comparison operator: {op}"
                if fatal_err is not None:
                    fatal_err.append(err_str)
                EXTERNAL.debug("%s", err_str)
                return False

            if result:
                INTERNAL.debug(
                    f"OK: {context}: {attr} passed '{op}' "
                    f"check (expected={expected}, value={val})")
            else:
                INTERNAL.debug(
                    f"ERROR: {context}: {attr} failed '{op}' "
                    f"check (expected={expected}, got={val})")
                success = False
        except (TypeError, ValueError) as e:
            err_str = f"{context}: {attr} - Type mismatch error" \
                f" for {op}: {e} (value={val}, expected={expected})"
            if fatal_err is not None:
                fatal_err.append(err_str)
            EXTERNAL.debug("%s", err_str)
            success = False

    return success


def validate_rule(
        attributes: Union[Dict[str, Any], Any],
        rule: Any,
        attr: str,
        context: str,
        inside_not: bool = False,
        fatal_err: Optional[List[str]] = None,
        plugin_ops: Optional[Dict[str, Callable]] = None,
        allow_missing_attrs: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate a rule. A rule can be a single comparison,
    or it can be an arbitrarily deep dict of logical operations
    with rules inside. This function will recursively validate
    rules within rules (for nested logical expressions) and return
    a tuple whose first member is a boolean indicating whether the rule
    passed or failed, and the second member is a list of errors that caused
    the rule to fail, if it failed. On success an empty list is returned in
    this position.
    """
    is_dict = isinstance(attributes, dict)

    if isinstance(rule, dict):
        if "and" in rule:
            all_passed = True
            all_failures = []
            for cond in rule["and"]:
                passed, failures = \
                    validate_rule(attributes, cond, attr, context,
                                  inside_not=inside_not,
                                  fatal_err=fatal_err,
                                  plugin_ops=plugin_ops)
                if not passed:
                    all_passed = False
                    all_failures.extend(failures)
            return all_passed, all_failures

        if "or" in rule:
            any_passed = False
            all_failures = []
            for cond in rule["or"]:
                passed, failures = \
                    validate_rule(attributes, cond, attr, context,
                                  inside_not=inside_not,
                                  fatal_err=fatal_err,
                                  plugin_ops=plugin_ops)
                if passed:
                    any_passed = True
                    break
                else:
                    all_failures.extend(failures)
            return any_passed, [] if any_passed else all_failures

        if "not" in rule:
            passed, failures = \
                validate_rule(attributes, rule["not"], attr, context,
                              inside_not=True,
                              fatal_err=fatal_err,
                              plugin_ops=plugin_ops)
            if passed:
                err_str = f"{context}: {attr} failed 'not' " \
                          f"condition: {rule['not']}"
                return False, [err_str]
            else:
                return True, []

        if is_dict:
            all_passed = True
            all_failures = []
            for attribute_name, condition in rule.items():
                if attribute_name not in attributes:
                    if not (inside_not and allow_missing_attrs):
                        err_str = \
                            f"{context}: unknown attribute: {attribute_name}"
                        if fatal_err is not None:
                            fatal_err.append(err_str)
                    all_passed = False
                else:
                    value = attributes[attribute_name]
                    block_fatal = []
                    result = compare(value, condition,
                                     attribute_name, context,
                                     fatal_err=block_fatal,
                                     plugin_ops=plugin_ops)
                    if not result and not inside_not:
                        err_str = f"{context}: {attribute_name} failed " \
                                  f"condition {condition}"
                        all_failures.append(err_str)
                    if block_fatal and fatal_err is not None:
                        fatal_err.extend(block_fatal)
                    all_passed = all_passed and result
            return all_passed, all_failures
        else:
            # Non-dict value (e.g., sysctl)
            block_fatal = []
            result = compare(attributes, rule, attr, context,
                             fatal_err=block_fatal,
                             plugin_ops=plugin_ops)
            if block_fatal and fatal_err is not None:
                fatal_err.extend(block_fatal)
            if not result and not inside_not:
                return False, [f"{context}: {attr} failed condition {rule}"]
            return result, []
    else:
        # Bare value, treated as implicit eq
        block_fatal = []
        result = compare(attributes, {"eq": rule}, attr, context,
                         fatal_err=block_fatal,
                         plugin_ops=plugin_ops)
        if block_fatal and fatal_err is not None:
            fatal_err.extend(block_fatal)
        if not result and not inside_not:
            return False, [f"{context}: {attr} failed condition eq {rule}"]
        return result, []
