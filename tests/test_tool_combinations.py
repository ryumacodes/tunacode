"""
Tests for tool combinations and workflows.
Tests realistic scenarios combining multiple tools.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.glob import glob
from tunacode.tools.grep import grep
from tunacode.tools.read_file import read_file
from tunacode.tools.write_file import write_file
from tunacode.tools.update_file import update_file
from tunacode.tools.list_dir import list_dir
from pydantic_ai import ModelRetry

pytestmark = pytest.mark.asyncio


class TestToolCombinations:
    """Test combinations of file operation tools."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_grep_read_update_workflow(self):
        """Test workflow: Grep → Read → Update."""
        # Create a project with multiple files containing TODOs
        project_files = {
            "src/auth.py": """
class AuthService:
    def login(self, username, password):
        # TODO: Implement proper authentication
        return True
    
    def logout(self):
        # TODO: Clear session data
        pass
""",
            "src/database.py": """
class Database:
    def connect(self):
        # TODO: Add connection pooling
        self.connection = None
    
    def query(self, sql):
        # TODO: Add query caching
        return []
""",
            "src/api.py": """
from flask import Flask

app = Flask(__name__)

@app.route('/users')
def get_users():
    # TODO: Implement user listing
    return {"users": []}
""",
            "tests/test_auth.py": """
def test_login():
    # TODO: Write actual tests
    assert True
"""
        }
        
        # Create all files
        for path, content in project_files.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            await write_file(path, content)
        
        # Step 1: Grep for all TODOs
        todo_files = await grep(r"TODO:", include_files="**/*.py", return_format="list", use_regex=True)
        assert len(todo_files) == 4
        
        # Step 2: Read each file and identify TODO patterns
        todo_updates = []
        for file_path in todo_files:
            content = await read_file(file_path)
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if "TODO:" in line:
                    # Extract the TODO comment
                    todo_text = line.strip()
                    if "authentication" in todo_text:
                        todo_updates.append((file_path, todo_text, "# Implemented: Using JWT tokens"))
                    elif "session data" in todo_text:
                        todo_updates.append((file_path, todo_text, "# Implemented: Redis session store"))
                    elif "connection pooling" in todo_text:
                        todo_updates.append((file_path, todo_text, "# Implemented: SQLAlchemy pool"))
        
        # Step 3: Update identified TODOs
        for file_path, target, patch in todo_updates:
            await update_file(file_path, target=target, patch=patch)
        
        # Step 4: Verify updates
        remaining_todos = await grep(r"TODO:", include_files="**/*.py", return_format="list", use_regex=True)
        assert len(remaining_todos) < len(todo_files)  # Some TODOs were resolved
        
        # Verify specific updates
        auth_content = await read_file("src/auth.py")
        assert "JWT tokens" in auth_content
        assert "Redis session store" in auth_content
    
    async def test_glob_batch_read_update(self):
        """Test workflow: Glob → Batch read → Batch update."""
        # Create configuration files for different environments
        configs = {
            "config.dev.json": '{"env": "development", "debug": true, "port": 3000}',
            "config.test.json": '{"env": "test", "debug": true, "port": 3001}',
            "config.staging.json": '{"env": "staging", "debug": false, "port": 3002}',
            "config.prod.json": '{"env": "production", "debug": false, "port": 8080}',
        }
        
        for filename, content in configs.items():
            await write_file(filename, content)
        
        # Step 1: Glob all config files
        config_files = await glob("config.*.json")
        assert len(config_files) == 4
        
        # Step 2: Batch read all configs
        config_contents = {}
        for config_file in config_files:
            content = await read_file(config_file)
            config_contents[config_file] = content
        
        # Step 3: Batch update - add API endpoint to all configs
        for config_file in config_files:
            # Update to add API endpoint before the closing brace
            await update_file(
                config_file,
                target='"}',
                patch='", "api_endpoint": "https://api.example.com"}'
            )
        
        # Step 4: Verify all configs were updated
        for config_file in config_files:
            content = await read_file(config_file)
            assert "api_endpoint" in content
            assert "https://api.example.com" in content
    
    async def test_create_populate_search_modify(self):
        """Test workflow: Create directory structure → Populate → Search → Modify."""
        # Step 1: Create a React-like project structure
        structure = [
            "src/components/Header.jsx",
            "src/components/Footer.jsx",
            "src/components/Button.jsx",
            "src/pages/Home.jsx",
            "src/pages/About.jsx",
            "src/utils/api.js",
            "src/utils/helpers.js",
            "src/styles/main.css",
            "src/styles/components.css",
            "public/index.html",
            "tests/Header.test.jsx",
            "tests/Button.test.jsx",
        ]
        
        # Step 2: Populate with content
        for file_path in structure:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            if file_path.endswith('.jsx'):
                # React component
                component_name = Path(file_path).stem
                content = f"""import React from 'react';

const {component_name} = () => {{
    return (
        <div className="{component_name.lower()}">
            <h1>{component_name} Component</h1>
        </div>
    );
}};

export default {component_name};
"""
            elif file_path.endswith('.js'):
                # JavaScript utility
                content = f"// Utility: {Path(file_path).stem}\n\nexport function util() {{\n    return 'utility';\n}}"
            elif file_path.endswith('.css'):
                # CSS file
                content = f"/* Styles for {Path(file_path).stem} */\n\n.container {{\n    margin: 0;\n}}"
            elif file_path.endswith('.html'):
                # HTML file
                content = "<!DOCTYPE html>\n<html><head><title>App</title></head><body><div id='root'></div></body></html>"
            else:
                # Test file
                content = f"// Test for {Path(file_path).stem}\n\ntest('renders', () => {{\n    expect(true).toBe(true);\n}});"
            
            await write_file(file_path, content)
        
        # Step 3: Search for React components
        jsx_files = await glob("**/*.jsx")
        assert len(jsx_files) == 7  # 5 components + 2 tests
        
        # Search for specific patterns
        components_with_classname = await grep(r'className=', include_files="**/*.jsx", return_format="list")
        assert len(components_with_classname) == 5  # All components have className
        
        # Step 4: Modify - Convert class components to functional (already functional, so update imports)
        for jsx_file in jsx_files:
            if not jsx_file.startswith('tests/'):
                # Add useState import to all components
                await update_file(
                    jsx_file,
                    target="import React from 'react';",
                    patch="import React, { useState } from 'react';"
                )
        
        # Verify modifications
        for jsx_file in jsx_files:
            if not jsx_file.startswith('tests/'):
                content = await read_file(jsx_file)
                assert "{ useState }" in content
    
    async def test_search_analyze_refactor_pattern(self):
        """Test pattern: Search for code patterns → Analyze → Refactor."""
        # Create Python modules with various import styles
        modules = {
            "old_style.py": """
import os
import sys
import json
from datetime import datetime
from collections import defaultdict

def process_data():
    data = json.loads('{}')
    return data
""",
            "mixed_style.py": """
import os, sys
from datetime import datetime, timedelta
import json as j
from collections import *

def analyze():
    return defaultdict(list)
""",
            "new_style.py": """
from datetime import datetime
from pathlib import Path
import json

def modern_function():
    return Path.home()
"""
        }
        
        for filename, content in modules.items():
            await write_file(filename, content)
        
        # Step 1: Search for import patterns
        files_with_imports = await grep(r"^import |^from .* import", include_files="*.py", return_format="list", use_regex=True)
        assert len(files_with_imports) == 3
        
        # Step 2: Analyze import styles
        needs_refactoring = []
        for file_path in files_with_imports:
            content = await read_file(file_path)
            lines = content.split('\n')
            
            for line in lines:
                if line.strip().startswith(('import', 'from')):
                    # Check for multiple imports on one line
                    if ',' in line and line.startswith('import'):
                        needs_refactoring.append((file_path, line))
                    # Check for wildcard imports
                    elif 'import *' in line:
                        needs_refactoring.append((file_path, line))
        
        # Step 3: Refactor problematic imports
        # Fix multiple imports on one line
        if needs_refactoring:
            file_path, bad_line = needs_refactoring[0]
            if ',' in bad_line:
                # Split comma-separated imports
                imports = bad_line.replace('import ', '').split(',')
                new_imports = '\n'.join(f'import {imp.strip()}' for imp in imports)
                await update_file(file_path, target=bad_line, patch=new_imports)
        
        # Verify refactoring
        if needs_refactoring:
            content = await read_file(needs_refactoring[0][0])
            assert 'import os, sys' not in content
    
    async def test_incremental_migration_workflow(self):
        """Test incremental code migration workflow."""
        # Create a JavaScript codebase to migrate to TypeScript
        js_files = {
            "src/user.js": """
function createUser(name, email) {
    return {
        id: Math.random(),
        name: name,
        email: email,
        createdAt: new Date()
    };
}

function validateEmail(email) {
    return email.includes('@');
}

module.exports = { createUser, validateEmail };
""",
            "src/product.js": """
class Product {
    constructor(name, price) {
        this.name = name;
        this.price = price;
        this.inStock = true;
    }
    
    applyDiscount(percentage) {
        this.price = this.price * (1 - percentage / 100);
    }
}

module.exports = Product;
""",
            "src/utils.js": """
function formatCurrency(amount) {
    return '$' + amount.toFixed(2);
}

function calculateTax(amount, rate) {
    return amount * rate;
}

module.exports = { formatCurrency, calculateTax };
"""
        }
        
        for path, content in js_files.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            await write_file(path, content)
        
        # Step 1: Find all JS files
        js_files_list = await glob("**/*.js")
        assert len(js_files_list) == 3
        
        # Step 2: Analyze each file for migration
        for js_file in js_files_list:
            content = await read_file(js_file)
            
            # Create TypeScript version
            ts_file = js_file.replace('.js', '.ts')
            ts_content = content
            
            # Add basic type annotations
            if 'createUser' in content:
                # Add interface for User
                interface = """interface User {
    id: number;
    name: string;
    email: string;
    createdAt: Date;
}

"""
                ts_content = interface + ts_content
                ts_content = ts_content.replace(
                    'function createUser(name, email)',
                    'function createUser(name: string, email: string): User'
                )
                ts_content = ts_content.replace(
                    'function validateEmail(email)',
                    'function validateEmail(email: string): boolean'
                )
            elif 'class Product' in content:
                # Add property declarations
                ts_content = ts_content.replace(
                    'class Product {',
                    '''class Product {
    name: string;
    price: number;
    inStock: boolean;
'''
                )
                ts_content = ts_content.replace(
                    'constructor(name, price)',
                    'constructor(name: string, price: number)'
                )
                ts_content = ts_content.replace(
                    'applyDiscount(percentage)',
                    'applyDiscount(percentage: number): void'
                )
            elif 'formatCurrency' in content:
                ts_content = ts_content.replace(
                    'function formatCurrency(amount)',
                    'function formatCurrency(amount: number): string'
                )
                ts_content = ts_content.replace(
                    'function calculateTax(amount, rate)',
                    'function calculateTax(amount: number, rate: number): number'
                )
            
            # Replace module.exports with export
            ts_content = ts_content.replace('module.exports = ', 'export ')
            
            # Write TypeScript file
            await write_file(ts_file, ts_content)
        
        # Step 3: Verify migration
        ts_files = await glob("**/*.ts")
        assert len(ts_files) == 3
        
        # Check type annotations were added
        user_ts = await read_file("src/user.ts")
        assert 'interface User' in user_ts
        assert 'string' in user_ts
        assert 'boolean' in user_ts
        
        product_ts = await read_file("src/product.ts")
        assert 'name: string' in product_ts
        assert 'price: number' in product_ts
    
    async def test_codebase_analysis_workflow(self):
        """Test analyzing a codebase structure and generating reports."""
        # Create a sample Python package
        package_structure = {
            "mypackage/__init__.py": "from .core import *\nfrom .utils import *",
            "mypackage/core.py": """
class Engine:
    def __init__(self):
        self.running = False
    
    def start(self):
        self.running = True
    
    def stop(self):
        self.running = False

class Processor:
    def process(self, data):
        return data.upper()
""",
            "mypackage/utils.py": """
def validate_input(value):
    if not value:
        raise ValueError("Empty value")
    return True

def format_output(data):
    return f"Output: {data}"
""",
            "mypackage/models.py": """
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str

@dataclass 
class Product:
    name: str
    price: float
""",
            "tests/test_core.py": """
from mypackage.core import Engine, Processor

def test_engine():
    engine = Engine()
    engine.start()
    assert engine.running

def test_processor():
    proc = Processor()
    assert proc.process("hello") == "HELLO"
""",
            "tests/test_utils.py": """
from mypackage.utils import validate_input, format_output

def test_validate():
    assert validate_input("test") == True

def test_format():
    assert format_output("data") == "Output: data"
"""
        }
        
        for path, content in package_structure.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            await write_file(path, content)
        
        # Step 1: Analyze package structure
        all_py_files = await glob("**/*.py")
        
        # Step 2: Find all classes
        class_files = await grep(r"^class \w+", include_files="**/*.py", return_format="list", use_regex=True)
        
        # Step 3: Find all functions
        function_files = await grep(r"^def \w+", include_files="**/*.py", return_format="list", use_regex=True)
        
        # Step 4: Find all tests
        test_files = await glob("**/test_*.py")
        
        # Step 5: Generate analysis report
        report = f"""# Codebase Analysis Report

## Overview
- Total Python files: {len(all_py_files)}
- Files with classes: {len(class_files)}
- Files with functions: {len(function_files)}
- Test files: {len(test_files)}

## Structure
"""
        
        # Analyze each module
        for py_file in sorted(all_py_files):
            if '__pycache__' not in py_file:
                content = await read_file(py_file)
                lines = content.split('\n')
                
                classes = [line.strip() for line in lines if line.strip().startswith('class ')]
                functions = [line.strip() for line in lines if line.strip().startswith('def ') and not line.strip().startswith('def __')]
                
                if classes or functions:
                    report += f"\n### {py_file}\n"
                    if classes:
                        report += f"- Classes: {len(classes)}\n"
                        for cls in classes:
                            report += f"  - {cls}\n"
                    if functions:
                        report += f"- Functions: {len(functions)}\n"
                        for func in functions:
                            report += f"  - {func}\n"
        
        # Write report
        await write_file("ANALYSIS.md", report)
        
        # Verify report was created
        report_content = await read_file("ANALYSIS.md")
        assert "Codebase Analysis Report" in report_content
        assert "Total Python files:" in report_content
        assert "class Engine" in report_content
        assert "def validate_input" in report_content