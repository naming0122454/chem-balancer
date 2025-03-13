import os
import logging
import re
from flask import Flask, render_template, request, jsonify
from chempy import balance_stoichiometry

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/balance', methods=['POST'])
def balance_equation():
    """Balance the chemical equation and count atoms."""
    equation = request.form.get('equation', '')
    
    # Remove spaces
    equation = equation.replace(" ", "")
    
    # Check if equation contains an arrow
    if '->' not in equation and '→' not in equation:
        return jsonify({
            'error': 'รูปแบบสมการไม่ถูกต้อง กรุณาใช้ -> หรือ → เพื่อแยกสารตั้งต้นและผลิตภัณฑ์'
        })
    
    # Standardize arrow to ->
    equation = equation.replace('→', '->')
    
    # Split equation into reactants and products
    sides = equation.split('->')
    if len(sides) != 2:
        return jsonify({
            'error': 'รูปแบบสมการไม่ถูกต้อง กรุณาใช้ลูกศร (->) เพียงหนึ่งตัวเพื่อแยกสารตั้งต้นและผลิตภัณฑ์'
        })
    
    reactants_str = sides[0].strip()
    products_str = sides[1].strip()
    
    # Split compounds by +
    reactants = reactants_str.split('+')
    products = products_str.split('+')
    
    # Create dictionaries from strings
    reactants_dict = {}
    products_dict = {}
    
    try:
        for reactant in reactants:
            reactant = reactant.strip()
            if reactant:
                reactants_dict[reactant] = 1
                
        for product in products:
            product = product.strip()
            if product:
                products_dict[product] = 1
        
        # Balance the equation
        reac, prod = balance_stoichiometry(reactants_dict, products_dict)
        
        # Convert any special number types to standard Python integers
        reac_dict = {k: int(v) for k, v in reac.items()}
        prod_dict = {k: int(v) for k, v in prod.items()}
        
        # Format the balanced equation
        balanced_reactants = [f"{'' if coeff == 1 else coeff}{compound}" for compound, coeff in reac_dict.items()]
        balanced_products = [f"{'' if coeff == 1 else coeff}{compound}" for compound, coeff in prod_dict.items()]
        
        balanced_equation = " + ".join(balanced_reactants) + " -> " + " + ".join(balanced_products)
        
        # Count atoms in original and balanced equations
        original_atom_count = count_atoms(reactants_dict, products_dict)
        balanced_atom_count = count_atoms(reac_dict, prod_dict)
        
        return jsonify({
            'success': True,
            'original_equation': equation,
            'balanced_equation': balanced_equation,
            'original_atom_count': original_atom_count,
            'balanced_atom_count': balanced_atom_count
        })
    
    except Exception as e:
        logging.error(f"Error balancing equation: {str(e)}")
        return jsonify({
            'error': f"ไม่สามารถดุลสมการได้ โปรดตรวจสอบข้อมูลที่ป้อน: {str(e)}"
        })

def count_atoms(reactants_dict, products_dict):
    """Count atoms in reactants and products."""
    reactants_atoms = {}
    products_atoms = {}
    
    # Count atoms in reactants
    for compound, coeff in reactants_dict.items():
        atoms = parse_compound(compound)
        for element, count in atoms.items():
            if element in reactants_atoms:
                reactants_atoms[element] += count * coeff
            else:
                reactants_atoms[element] = count * coeff
    
    # Count atoms in products
    for compound, coeff in products_dict.items():
        atoms = parse_compound(compound)
        for element, count in atoms.items():
            if element in products_atoms:
                products_atoms[element] += count * coeff
            else:
                products_atoms[element] = count * coeff
    
    return {
        'reactants': reactants_atoms,
        'products': products_atoms
    }

def parse_compound(compound):
    """Parse a chemical compound and count atoms."""
    # Regex to match element symbols followed by optional numbers
    pattern = r'([A-Z][a-z]*)(\d*)'
    matches = re.findall(pattern, compound)
    
    atoms = {}
    for element, count in matches:
        count = int(count) if count else 1
        if element in atoms:
            atoms[element] += count
        else:
            atoms[element] = count
    
    return atoms

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)