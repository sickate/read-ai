import random
import itertools
import re
from typing import List, Tuple, Optional, Set
import ast
import operator
import math

class Game24:
    """24点游戏类"""
    
    def __init__(self):
        # 扑克牌数值映射
        self.card_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
            'J': 11, 'Q': 12, 'K': 13, 'A': 1
        }
        self.card_names = list(self.card_values.keys())
        
        # 支持的运算符
        self.operators = ['+', '-', '*', '/', '**']
        self.operator_functions = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '**': operator.pow
        }
    
    def generate_cards(self, num_cards: int = 4) -> List[str]:
        """随机生成指定数量的卡牌"""
        return random.choices(self.card_names, k=num_cards)
    
    def get_card_values(self, cards: List[str]) -> List[int]:
        """获取卡牌对应的数值"""
        return [self.card_values[card] for card in cards]
    
    def safe_eval(self, expression: str, allowed_numbers: Set[float]) -> Optional[float]:
        """安全地计算表达式，只允许特定的数字和运算符"""
        try:
            # 解析表达式为AST
            tree = ast.parse(expression, mode='eval')
            
            # 验证表达式的安全性
            if not self._is_safe_expression(tree.body, allowed_numbers):
                return None
            
            # 计算表达式
            result = eval(expression)
            
            # 检查结果是否为数字
            if isinstance(result, (int, float)) and not math.isnan(result) and not math.isinf(result):
                return float(result)
            return None
            
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
            return None
    
    def _is_safe_expression(self, node, allowed_numbers: Set[float]) -> bool:
        """检查AST节点是否安全"""
        if isinstance(node, ast.Constant):
            # 检查数字是否在允许的范围内
            if isinstance(node.value, (int, float)):
                return float(node.value) in allowed_numbers
            return False
        
        elif isinstance(node, ast.BinOp):
            # 检查二元运算符
            allowed_ops = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
            if not isinstance(node.op, allowed_ops):
                return False
            return (self._is_safe_expression(node.left, allowed_numbers) and 
                   self._is_safe_expression(node.right, allowed_numbers))
        
        elif isinstance(node, ast.UnaryOp):
            # 检查一元运算符（负号和开方）
            if isinstance(node.op, ast.USub):
                return self._is_safe_expression(node.operand, allowed_numbers)
            elif isinstance(node.op, ast.UAdd):
                return self._is_safe_expression(node.operand, allowed_numbers)
            return False
        
        elif isinstance(node, ast.Call):
            # 允许开方函数
            if (isinstance(node.func, ast.Name) and 
                node.func.id in ['sqrt', 'pow'] and 
                len(node.args) >= 1):
                return all(self._is_safe_expression(arg, allowed_numbers) for arg in node.args)
            return False
        
        elif isinstance(node, ast.Name):
            # 允许特定的函数名
            return node.id in ['sqrt', 'pow']
        
        return False
    
    def verify_answer(self, expression: str, cards: List[str], target: int = 24) -> bool:
        """验证用户答案是否正确"""
        try:
            # 获取卡牌数值
            card_values = self.get_card_values(cards)
            allowed_numbers = set(map(float, card_values))
            
            # 先将表达式中的卡牌名称替换为数值
            # 按卡牌名称长度从长到短排序，避免替换冲突（如"10"和"1"）
            processed_expr = expression
            sorted_cards = sorted(self.card_values.items(), key=lambda x: len(x[0]), reverse=True)
            for card, value in sorted_cards:
                processed_expr = processed_expr.replace(card, str(value))
            
            # 预处理表达式，添加数学函数支持
            processed_expr = processed_expr.replace('sqrt', 'math.sqrt').replace('pow', 'math.pow')
            
            # 计算结果
            result = self.safe_eval(processed_expr, allowed_numbers)
            
            if result is None:
                return False
            
            # 检查是否接近目标值（允许浮点数误差）
            return abs(result - target) < 1e-9
            
        except Exception:
            return False
    
    def solve_24(self, cards: List[str], target: int = 24) -> List[str]:
        """自动求解24点，返回所有可能的解答"""
        card_values = self.get_card_values(cards)
        solutions = []
        
        # 限制运算符以提高效率
        basic_operators = ['+', '-', '*', '/']
        
        # 生成所有可能的数字排列
        for perm in itertools.permutations(card_values):
            # 生成所有可能的运算符组合 (只使用基本运算符)
            for ops in itertools.product(basic_operators, repeat=len(perm)-1):
                # 生成所有可能的括号组合
                expressions = self._generate_expressions(perm, ops)
                
                for expr in expressions:
                    try:
                        result = eval(expr)
                        if isinstance(result, (int, float)) and abs(result - target) < 1e-9:
                            # 将数值替换回卡牌名称
                            display_expr = self._replace_values_with_cards(expr, perm, cards, card_values)
                            if display_expr not in solutions:
                                solutions.append(display_expr)
                                
                        # 限制解答数量以提高效率
                        if len(solutions) >= 5:
                            return solutions
                            
                    except (ZeroDivisionError, OverflowError, ValueError, TypeError):
                        continue
        
        return solutions
    
    def _generate_expressions(self, numbers: Tuple[int, ...], operators: Tuple[str, ...]) -> List[str]:
        """生成所有可能的表达式（包括不同的括号组合）"""
        if len(numbers) == 1:
            return [str(numbers[0])]
        
        expressions = []
        n = len(numbers)
        
        if n == 2:
            expressions.append(f"{numbers[0]} {operators[0]} {numbers[1]}")
        elif n == 3:
            # ((a op b) op c) 和 (a op (b op c))
            expressions.extend([
                f"(({numbers[0]} {operators[0]} {numbers[1]}) {operators[1]} {numbers[2]})",
                f"({numbers[0]} {operators[0]} ({numbers[1]} {operators[1]} {numbers[2]}))"
            ])
        elif n == 4:
            # 五种不同的括号组合
            expressions.extend([
                f"((({numbers[0]} {operators[0]} {numbers[1]}) {operators[1]} {numbers[2]}) {operators[2]} {numbers[3]})",
                f"(({numbers[0]} {operators[0]} {numbers[1]}) {operators[1]} ({numbers[2]} {operators[2]} {numbers[3]}))",
                f"(({numbers[0]} {operators[0]} ({numbers[1]} {operators[1]} {numbers[2]})) {operators[2]} {numbers[3]})",
                f"({numbers[0]} {operators[0]} (({numbers[1]} {operators[1]} {numbers[2]}) {operators[2]} {numbers[3]}))",
                f"({numbers[0]} {operators[0]} ({numbers[1]} {operators[1]} ({numbers[2]} {operators[2]} {numbers[3]})))"
            ])
        elif n == 5:
            # 5张牌的情况，生成更多组合（简化版本）
            expressions.extend([
                f"(((({numbers[0]} {operators[0]} {numbers[1]}) {operators[1]} {numbers[2]}) {operators[2]} {numbers[3]}) {operators[3]} {numbers[4]})",
                f"((({numbers[0]} {operators[0]} {numbers[1]}) {operators[1]} {numbers[2]}) {operators[2]} ({numbers[3]} {operators[3]} {numbers[4]}))",
                f"(({numbers[0]} {operators[0]} {numbers[1]}) {operators[1]} (({numbers[2]} {operators[2]} {numbers[3]}) {operators[3]} {numbers[4]}))",
                f"(({numbers[0]} {operators[0]} ({numbers[1]} {operators[1]} {numbers[2]})) {operators[2]} ({numbers[3]} {operators[3]} {numbers[4]}))",
                f"({numbers[0]} {operators[0]} ((({numbers[1]} {operators[1]} {numbers[2]}) {operators[2]} {numbers[3]}) {operators[3]} {numbers[4]}))"
            ])
        
        return expressions
    
    def _replace_values_with_cards(self, expression: str, values: Tuple[int, ...], cards: List[str], card_values: List[int]) -> str:
        """将表达式中的数值替换为对应的卡牌名称"""
        result = expression
        
        # 创建值到卡牌的映射
        value_to_card = {}
        for i, val in enumerate(values):
            # 找到对应的卡牌
            for j, card_val in enumerate(card_values):
                if val == card_val and j not in value_to_card.values():
                    value_to_card[val] = cards[j]
                    break
        
        # 按数值的字符串长度从长到短排序，避免替换冲突
        # 例如：先替换"10"再替换"1"，避免"10"被误替换为"A0"
        sorted_values = sorted(value_to_card.keys(), key=lambda x: len(str(x)), reverse=True)
        
        for val in sorted_values:
            # 使用词边界替换，确保精确匹配
            pattern = r'\b' + str(val) + r'\b'
            result = re.sub(pattern, value_to_card[val], result)
        
        return result
    
    def has_solution(self, cards: List[str], target: int = 24) -> bool:
        """检查给定的卡牌组合是否有解"""
        solutions = self.solve_24(cards, target)
        return len(solutions) > 0
    
    def generate_solvable_cards(self, num_cards: int = 4, target: int = 24, max_attempts: int = 100) -> List[str]:
        """生成有解的卡牌组合"""
        for _ in range(max_attempts):
            cards = self.generate_cards(num_cards)
            if self.has_solution(cards, target):
                return cards
        
                # 如果找不到有解的组合，返回一个已知有解的组合
        known_solutions = {
            4: ['4', 'A', '8', '7'],  # (8-4) * (7-A) = 24
            5: ['3', '3', '8', '8', '3']  # 3 * 8 + 3 - 3 = 24
        }
        return known_solutions.get(num_cards, self.generate_cards(num_cards))


# 创建全局游戏实例
game_24 = Game24() 