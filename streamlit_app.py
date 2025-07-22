import streamlit as st
import requests
import pandas as pd
from typing import Dict, List, Optional

BACKEND_URL = "https://splitwise-pzwt.onrender.com/api/v1"

st.set_page_config(
    page_title="SplitEase",
    page_icon="💚",
    layout="wide"
)

# Dark theme CSS
st.markdown("""
<style>
body, .stApp { background: #181c20 !important; color: #f3f4f6 !important; }
.section-header { font-size: 1.3rem; font-weight: 600; margin-top: 1.5em; margin-bottom: 0.5em; color: #f3f4f6; }
.card { background: #23272b; border-radius: 10px; box-shadow: 0 2px 8px #111; padding: 1.2em 1.5em; margin-bottom: 1.2em; color: #f3f4f6; }
.stButton > button { width: 100%; border-radius: 8px; font-weight: 600; font-size: 1.1em; background: #23272b; color: #f3f4f6; border: 1px solid #333; }
.stButton > button:hover { background: #31363b; }
.stRadio > div { flex-direction: row; }
.stTabs [data-baseweb="tab-list"] { background: #23272b; border-radius: 8px; }
.stTabs [data-baseweb="tab"] { font-size: 1.1em; color: #f3f4f6; }
.stTabs [aria-selected="true"] { background: #31363b !important; color: #fff !important; }
input, select, textarea, .stTextInput > div > input, .stNumberInput > div > input { background: #23272b !important; color: #f3f4f6 !important; border: 1px solid #333 !important; }
.validation-error { color: #ff6b6b; font-size: 0.9em; margin-top: 0.2em; }
.validation-success { color: #51cf66; font-size: 0.9em; margin-top: 0.2em; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'people_list' not in st.session_state:
    st.session_state.people_list = []
if 'expenses_data' not in st.session_state:
    st.session_state.expenses_data = []

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API request with proper error handling"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        response.raise_for_status()
        resp_json = response.json()
        
        # Handle different response formats
        if isinstance(resp_json, dict) and 'success' in resp_json:
            return resp_json
        elif isinstance(resp_json, list):
            return {"success": True, "data": resp_json}
        else:
            return {"success": True, "data": resp_json}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Network error: {str(e)}", "data": None}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}

@st.cache_data(ttl=30)
def get_all_people() -> List[str]:
    """Get all people from backend with caching"""
    response = make_api_request("/people")
    if response.get("success") and response.get("data"):
        people_data = response["data"]
        if isinstance(people_data, dict) and "people" in people_data:
            return people_data["people"]
        elif isinstance(people_data, list):
            return people_data
    return []

@st.cache_data(ttl=30)
def get_all_expenses() -> List[Dict]:
    """Get all expenses from backend with caching"""
    response = make_api_request("/expenses")
    if response.get("success") and response.get("data"):
        return response["data"]
    return []

def get_all_groups(expenses: List[Dict]) -> List[str]:
    """Extract unique groups from expenses"""
    groups = set()
    for exp in expenses:
        group = exp.get('group')
        if group and group.strip():
            groups.add(group.strip())
    return sorted(list(groups))

def validate_split_shares(split_type: str, shares: Dict[str, float], participants: List[str], amount: float) -> tuple[bool, str]:
    """Validate split shares based on type"""
    if split_type == "equal":
        return True, "Equal split - no manual shares needed"
    
    if not shares:
        return False, f"Shares required for {split_type} split"
    
    # Check all participants have shares
    missing = set(participants) - set(shares.keys())
    if missing:
        return False, f"Missing shares for: {', '.join(missing)}"
    
    if split_type == "percentage":
        total = sum(shares.values())
        if abs(total - 100) > 0.01:
            return False, f"Percentages must sum to 100% (currently {total:.1f}%)"
        return True, f"Percentages sum to {total:.1f}% ✓"
    
    elif split_type == "exact":
        total = sum(shares.values())
        if abs(total - amount) > 0.01:
            return False, f"Exact amounts must sum to ₹{amount:.2f} (currently ₹{total:.2f})"
        return True, f"Exact amounts sum to ₹{total:.2f} ✓"
    
    return True, ""

def show_add_expense_tab():
    st.markdown("<div class='section-header'>Add a New Expense</div>", unsafe_allow_html=True)
    
    # Load people and expenses for dropdowns
    people_list = get_all_people()
    expenses_data = get_all_expenses()
    groups_list = get_all_groups(expenses_data)
    
    # Basic expense info - OUTSIDE form so radio button can trigger changes
    col1, col2 = st.columns(2)
    
    with col1:
        amount = st.number_input(
            "Amount (₹)", 
            min_value=0.01, 
            step=0.01, 
            format="%.2f",
            help="Total amount for this expense",
            key="amount_input"
        )
        description = st.text_input(
            "Description", 
            placeholder="e.g., Dinner at restaurant",
            help="What was this expense for?",
            key="description_input"
        )
    
    with col2:
        category = st.text_input(
            "Category", 
            placeholder="e.g., Food, Travel",
            help="Optional: categorize this expense",
            key="category_input"
        )
        group = st.text_input(
            "Group", 
            placeholder="e.g., Trip to Goa",
            help="Optional: group this expense belongs to",
            key="group_input"
        )
    
    st.markdown("<div class='section-header' style='font-size:1.1em;'>Who Paid?</div>", unsafe_allow_html=True)
    
    # Payer selection - OUTSIDE form
    col1, col2 = st.columns(2)
    with col1:
        selected_payer = st.selectbox(
            "Select from existing people:",
            options=[""] + people_list,
            help="Choose from people who have participated in expenses before",
            key="selected_payer"
        )
    with col2:
        new_payer = st.text_input(
            "Or add new person:",
            placeholder="Type new name here",
            help="Add a new person as the payer",
            key="new_payer"
        )
    
    # Determine final payer
    paid_by = new_payer.strip() if new_payer.strip() else selected_payer
    
    st.markdown("<div class='section-header' style='font-size:1.1em;'>Participants</div>", unsafe_allow_html=True)
    
    # Participants selection - OUTSIDE form
    selected_participants = st.multiselect(
        "Select from existing people:",
        options=people_list,
        help="Choose from people who have participated in expenses before",
        key="selected_participants"
    )
    
    new_participants = st.text_input(
        "Add new participants (comma separated):",
        placeholder="John, Mary, Alex",
        help="Type new names separated by commas",
        key="new_participants"
    )
    
    # Combine participants
    all_participants = list(selected_participants)
    if new_participants.strip():
        new_names = [name.strip() for name in new_participants.split(",") if name.strip()]
        for name in new_names:
            if name not in all_participants:
                all_participants.append(name)
    
    # Ensure payer is in participants
    if paid_by and paid_by not in all_participants:
        all_participants.append(paid_by)
    
    st.markdown("<div class='section-header' style='font-size:1.1em;'>Split Method</div>", unsafe_allow_html=True)
    
    # Split type selection - OUTSIDE form so it triggers immediate UI changes
    split_type = st.radio(
        "How should this expense be split?",
        options=["equal", "percentage", "exact"],
        format_func=lambda x: {
            "equal": "Equal Split",
            "percentage": "Percentage Split", 
            "exact": "Exact Amount Split"
        }[x],
        horizontal=True,
        key="split_type_radio"
    )
    
    # Dynamic share inputs - OUTSIDE form so they appear immediately
    shares = {}
    share_validation_msg = ""
    is_shares_valid = True
    
    # Show share inputs immediately when percentage or exact is selected AND participants exist
    if all_participants and split_type in ["percentage", "exact"]:
        st.markdown(f"<div style='margin-top:1em; margin-bottom:0.5em;'><b>Set {split_type.title()} Shares for Each Participant</b></div>", unsafe_allow_html=True)
        
        # Create a more organized layout for share inputs
        num_participants = len(all_participants)
        
        if num_participants <= 3:
            # Single row for 3 or fewer participants
            cols = st.columns(num_participants)
            for i, participant in enumerate(all_participants):
                with cols[i]:
                    if split_type == "percentage":
                        default_val = round(100.0 / num_participants, 2)
                        shares[participant] = st.number_input(
                            f"{participant}",
                            min_value=0.0,
                            max_value=100.0,
                            value=default_val,
                            step=0.1,
                            format="%.1f",
                            key=f"pct_{participant}_{len(all_participants)}",
                            help=f"Percentage for {participant}"
                        )
                        st.caption("(%)")
                    else:  # exact
                        default_val = round(amount / num_participants, 2) if amount > 0 else 0.0
                        shares[participant] = st.number_input(
                            f"{participant}",
                            min_value=0.0,
                            value=default_val,
                            step=0.01,
                            format="%.2f",
                            key=f"exact_{participant}_{len(all_participants)}",
                            help=f"Exact amount for {participant}"
                        )
                        st.caption("(₹)")
        else:
            # Multiple rows for more than 3 participants
            cols_per_row = 3
            for i in range(0, num_participants, cols_per_row):
                cols = st.columns(cols_per_row)
                for j, participant in enumerate(all_participants[i:i+cols_per_row]):
                    with cols[j]:
                        if split_type == "percentage":
                            default_val = round(100.0 / num_participants, 2)
                            shares[participant] = st.number_input(
                                f"{participant}",
                                min_value=0.0,
                                max_value=100.0,
                                value=default_val,
                                step=0.1,
                                format="%.1f",
                                key=f"pct_{participant}_{i+j}_{len(all_participants)}",
                                help=f"Percentage for {participant}"
                            )
                            st.caption("(%)")
                        else:  # exact
                            default_val = round(amount / num_participants, 2) if amount > 0 else 0.0
                            shares[participant] = st.number_input(
                                f"{participant}",
                                min_value=0.0,
                                value=default_val,
                                step=0.01,
                                format="%.2f",
                                key=f"exact_{participant}_{i+j}_{len(all_participants)}",
                                help=f"Exact amount for {participant}"
                            )
                            st.caption("(₹)")
        
        # Show running total and validation immediately
        if shares:
            total = sum(shares.values())
            if split_type == "percentage":
                st.markdown(f"<div style='margin-top:0.5em; padding:0.5em; background:#2a2e33; border-radius:5px;'><b>Total: {total:.1f}%</b> (Target: 100%)</div>", unsafe_allow_html=True)
            else:  # exact
                st.markdown(f"<div style='margin-top:0.5em; padding:0.5em; background:#2a2e33; border-radius:5px;'><b>Total: ₹{total:.2f}</b> (Target: ₹{amount:.2f})</div>", unsafe_allow_html=True)
            
            # Real-time validation feedback
            is_shares_valid, validation_msg = validate_split_shares(split_type, shares, all_participants, amount)
            if validation_msg:
                if is_shares_valid:
                    st.markdown(f"<div class='validation-success'>✅ {validation_msg}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='validation-error'>❌ {validation_msg}</div>", unsafe_allow_html=True)
                    share_validation_msg = validation_msg
    
    elif split_type in ["percentage", "exact"] and not all_participants:
        # Show message when split type requires participants but none are selected
        st.warning(f"⚠️ Please add participants first to set up {split_type} split")
    
    # Add some spacing before the form
    st.markdown("<br>", unsafe_allow_html=True)
    
    # NOW the form - only for submission, all inputs are already collected above
    with st.form("add_expense_form", clear_on_submit=True):
        # Only show review section if we have enough information
        if amount and description and paid_by and all_participants:
            st.markdown("""
            <div style='margin-bottom:1.5em; padding:1.2em; background:#2a2e33; border-radius:8px; border:1px solid #444;'>
                <h4 style='margin-top:0; color:#51cf66;'>📋 Review Your Expense</h4>
            """, unsafe_allow_html=True)
            
            # Create two columns for better layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**💰 Amount:** ₹{amount:.2f}")
                st.markdown(f"**📝 Description:** {description}")
                st.markdown(f"**💳 Paid by:** {paid_by}")
                st.markdown(f"**🔄 Split Type:** {split_type.title()}")
            
            with col2:
                st.markdown(f"**👥 Participants:** {', '.join(all_participants)}")
                if category:
                    st.markdown(f"**🏷️ Category:** {category}")
                if group:
                    st.markdown(f"**👨‍👩‍👧‍👦 Group:** {group}")
            
            # Show shares if applicable
            if split_type in ["percentage", "exact"] and shares:
                st.markdown("**📊 Individual Shares:**")
                share_cols = st.columns(min(4, len(shares)))
                for i, (participant, share) in enumerate(shares.items()):
                    with share_cols[i % len(share_cols)]:
                        if split_type == "percentage":
                            st.markdown(f"• **{participant}:** {share:.1f}%")
                        else:
                            st.markdown(f"• **{participant}:** ₹{share:.2f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Show a helpful message when info is missing
            st.info("ℹ️ **Fill in the required fields above to see your expense summary:**")
            missing_fields = []
            if not amount or amount <= 0:
                missing_fields.append("Amount")
            if not description.strip():
                missing_fields.append("Description")
            if not paid_by.strip():
                missing_fields.append("Who Paid")
            if not all_participants:
                missing_fields.append("Participants")
            
            if missing_fields:
                st.markdown(f"**Missing:** {', '.join(missing_fields)}")
        
        # Submit button
        submitted = st.form_submit_button("➕ Add Expense", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            errors = []
            
            if not amount or amount <= 0:
                errors.append("Amount must be positive")
            
            if not description.strip():
                errors.append("Description is required")
            
            if not paid_by.strip():
                errors.append("Please specify who paid")
            
            if not all_participants:
                errors.append("At least one participant is required")
            
            if paid_by and paid_by not in all_participants:
                errors.append("Payer must be one of the participants")
            
            # Validate shares for non-equal splits
            if split_type in ["percentage", "exact"]:
                if not shares:
                    errors.append(f"Please set {split_type} shares for all participants")
                else:
                    is_valid, validation_msg = validate_split_shares(split_type, shares, all_participants, amount)
                    if not is_valid:
                        errors.append(validation_msg)
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Prepare expense data - JSON formation
                expense_data = {
                    "amount": amount,
                    "description": description,
                    "paid_by": paid_by,
                    "participants": all_participants,
                    "split_type": split_type
                }
                
                # Add optional fields
                if category.strip():
                    expense_data["category"] = category.strip()
                
                if group.strip():
                    expense_data["group"] = group.strip()
                
                # Add shares for non-equal splits
                if split_type in ["percentage", "exact"] and shares:
                    expense_data["shares"] = shares
                
                # Debug: Show the JSON being sent
                with st.expander("🔍 Debug: JSON being sent to API"):
                    st.json(expense_data)
                
                # Submit to backend
                with st.spinner("Adding expense..."):
                    response = make_api_request("/expenses", method="POST", data=expense_data)
                    
                    if response.get("success"):
                        st.success("✅ Expense added successfully!")
                        # Clear cache to refresh data
                        get_all_people.clear()
                        get_all_expenses.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add expense: {response.get('message', 'Unknown error')}")

def show_edit_delete_section():
    """Edit and Delete existing expenses section"""
    st.markdown("<div class='section-header'>Edit / Delete Existing Expense</div>", unsafe_allow_html=True)
    
    # Load all expenses
    expenses = get_all_expenses()
    people_list = get_all_people()
    
    if not expenses:
        st.info("📝 No expenses found. Add some expenses first to edit or delete them.")
        return
    
    # Create expense options for selectbox
    expense_options = []
    expense_map = {}
    for exp in expenses:
        option_text = f"₹{exp['amount']:.2f} - {exp['description']} (paid by {exp['paid_by']})"
        expense_options.append(option_text)
        expense_map[option_text] = exp
    
    # Expense selection
    selected_expense_text = st.selectbox(
        "Select an expense to edit or delete:",
        options=[""] + expense_options,
        help="Choose an expense to modify or remove"
    )
    
    if not selected_expense_text:
        st.info("👆 Select an expense above to edit or delete it")
        return
    
    selected_expense = expense_map[selected_expense_text]
    
    # Create two tabs for Edit and Delete
    tab1, tab2 = st.tabs(["✏️ Edit Expense", "🗑️ Delete Expense"])
    
    with tab1:
        st.markdown("**Edit the selected expense:**")
        
        # MOVE ALL INPUTS OUTSIDE FORM - Same as Add Expense logic
        col1, col2 = st.columns(2)
        
        with col1:
            edit_amount = st.number_input(
                "Amount (₹)", 
                min_value=0.01, 
                step=0.01, 
                format="%.2f",
                value=float(selected_expense['amount']),
                help="Total amount for this expense",
                key="edit_amount_input"
            )
            edit_description = st.text_input(
                "Description", 
                value=selected_expense['description'],
                help="What was this expense for?",
                key="edit_description_input"
            )
        
        with col2:
            edit_category = st.text_input(
                "Category", 
                value=selected_expense.get('category', ''),
                help="Optional: categorize this expense",
                key="edit_category_input"
            )
            edit_group = st.text_input(
                "Group", 
                value=selected_expense.get('group', ''),
                help="Optional: group this expense belongs to",
                key="edit_group_input"
            )
        
        # Payer selection - OUTSIDE form
        st.markdown("<div class='section-header' style='font-size:1.1em;'>Who Paid?</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            current_payer = selected_expense['paid_by']
            payer_options = people_list if current_payer in people_list else [current_payer] + people_list
            edit_paid_by = st.selectbox(
                "Select from existing people:",
                options=payer_options,
                index=payer_options.index(current_payer) if current_payer in payer_options else 0,
                help="Who paid for this expense",
                key="edit_selected_payer"
            )
        with col2:
            edit_new_payer = st.text_input(
                "Or add new person:",
                placeholder="Type new name here",
                help="Add a new person as the payer",
                key="edit_new_payer"
            )
        
        final_payer = edit_new_payer.strip() if edit_new_payer.strip() else edit_paid_by
        
        # Participants selection - OUTSIDE form
        st.markdown("<div class='section-header' style='font-size:1.1em;'>Participants</div>", unsafe_allow_html=True)
        current_participants = selected_expense.get('participants', [])
        edit_participants = st.multiselect(
            "Select from existing people:",
            options=people_list,
            default=[p for p in current_participants if p in people_list],
            help="Who participated in this expense",
            key="edit_selected_participants"
        )
        
        edit_new_participants = st.text_input(
            "Add new participants (comma separated):",
            placeholder="John, Mary, Alex",
            help="Add new people (comma separated)",
            key="edit_new_participants"
        )
        
        # Combine participants
        all_edit_participants = list(edit_participants)
        if edit_new_participants.strip():
            new_names = [name.strip() for name in edit_new_participants.split(",") if name.strip()]
            for name in new_names:
                if name not in all_edit_participants:
                    all_edit_participants.append(name)
        
        # Add any missing participants from original expense
        for participant in current_participants:
            if participant not in all_edit_participants:
                all_edit_participants.append(participant)
        
        # Ensure payer is in participants
        if final_payer and final_payer not in all_edit_participants:
            all_edit_participants.append(final_payer)
        
        # Split type selection - OUTSIDE form
        st.markdown("<div class='section-header' style='font-size:1.1em;'>Split Method</div>", unsafe_allow_html=True)
        current_split_type = selected_expense.get('split_type', 'equal')
        edit_split_type = st.radio(
            "How should this expense be split?",
            options=["equal", "percentage", "exact"],
            index=["equal", "percentage", "exact"].index(current_split_type),
            format_func=lambda x: {
                "equal": "Equal Split",
                "percentage": "Percentage Split", 
                "exact": "Exact Amount Split"
            }[x],
            horizontal=True,
            key="edit_split_type_radio"
        )
        
        # Dynamic share inputs - OUTSIDE form so they appear immediately
        edit_shares = {}
        edit_shares_valid = True
        
        # Show share inputs immediately when percentage or exact is selected AND participants exist
        if all_edit_participants and edit_split_type in ["percentage", "exact"]:
            st.markdown(f"<div style='margin-top:1em; margin-bottom:0.5em;'><b>Set {edit_split_type.title()} Shares for Each Participant</b></div>", unsafe_allow_html=True)
            
            current_shares = selected_expense.get('shares', {})
            num_participants = len(all_edit_participants)
            
            if num_participants <= 3:
                # Single row for 3 or fewer participants
                cols = st.columns(num_participants)
                for i, participant in enumerate(all_edit_participants):
                    with cols[i]:
                        if edit_split_type == "percentage":
                            default_val = current_shares.get(participant, round(100.0 / num_participants, 2))
                            edit_shares[participant] = st.number_input(
                                f"{participant}",
                                min_value=0.0,
                                max_value=100.0,
                                value=float(default_val),
                                step=0.1,
                                format="%.1f",
                                key=f"edit_pct_{participant}_{len(all_edit_participants)}",
                                help=f"Percentage for {participant}"
                            )
                            st.caption("(%)")
                        else:  # exact
                            default_val = current_shares.get(participant, round(edit_amount / num_participants, 2))
                            edit_shares[participant] = st.number_input(
                                f"{participant}",
                                min_value=0.0,
                                value=float(default_val),
                                step=0.01,
                                format="%.2f",
                                key=f"edit_exact_{participant}_{len(all_edit_participants)}",
                                help=f"Exact amount for {participant}"
                            )
                            st.caption("(₹)")
            else:
                # Multiple rows for more than 3 participants
                cols_per_row = 3
                for i in range(0, num_participants, cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, participant in enumerate(all_edit_participants[i:i+cols_per_row]):
                        with cols[j]:
                            if edit_split_type == "percentage":
                                default_val = current_shares.get(participant, round(100.0 / num_participants, 2))
                                edit_shares[participant] = st.number_input(
                                    f"{participant}",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(default_val),
                                    step=0.1,
                                    format="%.1f",
                                    key=f"edit_pct_{participant}_{i+j}_{len(all_edit_participants)}",
                                    help=f"Percentage for {participant}"
                                )
                                st.caption("(%)")
                            else:  # exact
                                default_val = current_shares.get(participant, round(edit_amount / num_participants, 2))
                                edit_shares[participant] = st.number_input(
                                    f"{participant}",
                                    min_value=0.0,
                                    value=float(default_val),
                                    step=0.01,
                                    format="%.2f",
                                    key=f"edit_exact_{participant}_{i+j}_{len(all_edit_participants)}",
                                    help=f"Exact amount for {participant}"
                                )
                                st.caption("(₹)")
        
        # Show running total and validation immediately
        if edit_shares:
            total = sum(edit_shares.values())
            if edit_split_type == "percentage":
                st.markdown(f"<div style='margin-top:0.5em; padding:0.5em; background:#2a2e33; border-radius:5px;'><b>Total: {total:.1f}%</b> (Target: 100%)</div>", unsafe_allow_html=True)
            else:  # exact
                st.markdown(f"<div style='margin-top:0.5em; padding:0.5em; background:#2a2e33; border-radius:5px;'><b>Total: ₹{total:.2f}</b> (Target: ₹{edit_amount:.2f})</div>", unsafe_allow_html=True)
            
            # Real-time validation feedback
            edit_shares_valid, validation_msg = validate_split_shares(edit_split_type, edit_shares, all_edit_participants, edit_amount)
            if validation_msg:
                if edit_shares_valid:
                    st.markdown(f"<div class='validation-success'>✅ {validation_msg}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='validation-error'>❌ {validation_msg}</div>", unsafe_allow_html=True)
        
        elif edit_split_type in ["percentage", "exact"] and not all_edit_participants:
            # Show message when split type requires participants but none are selected
            st.warning(f"⚠️ Please add participants first to set up {edit_split_type} split")
        
        # Add some spacing before the form
        st.markdown("<br>", unsafe_allow_html=True)
        
        # NOW the form - only for submission
        with st.form("edit_expense_form"):
            # Only show review section if we have enough information
            if edit_amount and edit_description and final_payer and all_edit_participants:
                st.markdown("""
                <div style='margin-bottom:1.5em; padding:1.2em; background:#2a2e33; border-radius:8px; border:1px solid #444;'>
                    <h4 style='margin-top:0; color:#51cf66;'>📋 Review Updated Expense</h4>
                """, unsafe_allow_html=True)
                
                # Create two columns for better layout
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**💰 Amount:** ₹{edit_amount:.2f}")
                    st.markdown(f"**📝 Description:** {edit_description}")
                    st.markdown(f"**💳 Paid by:** {final_payer}")
                    st.markdown(f"**🔄 Split Type:** {edit_split_type.title()}")
                
                with col2:
                    st.markdown(f"**👥 Participants:** {', '.join(all_edit_participants)}")
                    if edit_category:
                        st.markdown(f"**🏷️ Category:** {edit_category}")
                    if edit_group:
                        st.markdown(f"**👨‍👩‍👧‍👦 Group:** {edit_group}")
            
            # Show shares if applicable
            if edit_split_type in ["percentage", "exact"] and edit_shares:
                st.markdown("**📊 Individual Shares:**")
                share_cols = st.columns(min(4, len(edit_shares)))
                for i, (participant, share) in enumerate(edit_shares.items()):
                    with share_cols[i % len(share_cols)]:
                        if edit_split_type == "percentage":
                            st.markdown(f"• **{participant}:** {share:.1f}%")
                        else:
                            st.markdown(f"• **{participant}:** ₹{share:.2f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            # Show a helpful message when info is missing
            missing_fields = []
            if not edit_amount or edit_amount <= 0:
                missing_fields.append("Amount")
            if not edit_description.strip():
                missing_fields.append("Description")
            if not final_payer.strip():
                missing_fields.append("Who Paid")
            if not all_edit_participants:
                missing_fields.append("Participants")
            
            if missing_fields:
                st.markdown(f"**Missing:** {', '.join(missing_fields)}")
            
            # Submit update button
            submitted_edit = st.form_submit_button("💾 Update Expense", use_container_width=True, type="primary")
            
            if submitted_edit:
                # Validation
                errors = []
                
                if not edit_amount or edit_amount <= 0:
                    errors.append("Amount must be positive")
                
                if not edit_description.strip():
                    errors.append("Description is required")
                
                if not final_payer.strip():
                    errors.append("Please specify who paid")
                
                if not all_edit_participants:
                    errors.append("At least one participant is required")
                
                if final_payer and final_payer not in all_edit_participants:
                    errors.append("Payer must be one of the participants")
                
                # Validate shares for non-equal splits
                if edit_split_type in ["percentage", "exact"]:
                    if not edit_shares:
                        errors.append(f"Please set {edit_split_type} shares for all participants")
                    else:
                        is_valid, validation_msg = validate_split_shares(edit_split_type, edit_shares, all_edit_participants, edit_amount)
                        if not is_valid:
                            errors.append(validation_msg)
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Prepare update data
                    update_data = {
                        "amount": edit_amount,
                        "description": edit_description,
                        "paid_by": final_payer,
                        "participants": all_edit_participants,
                        "split_type": edit_split_type
                    }
                    
                    if edit_category.strip():
                        update_data["category"] = edit_category.strip()
                    
                    if edit_group.strip():
                        update_data["group"] = edit_group.strip()
                    
                    if edit_split_type in ["percentage", "exact"] and edit_shares:
                        update_data["shares"] = edit_shares
                    
                    # Debug: Show the JSON being sent
                    with st.expander("🔍 Debug: JSON being sent to API"):
                        st.json(update_data)
                    
                    # Submit update
                    with st.spinner("Updating expense..."):
                        response = make_api_request(f"/expenses/{selected_expense['id']}", method="PUT", data=update_data)
                        
                        if response.get("success"):
                            st.success("✅ Expense updated successfully!")
                            # Clear cache to refresh data
                            get_all_people.clear()
                            get_all_expenses.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update expense: {response.get('message', 'Unknown error')}")
    
    with tab2:
        st.markdown("**Delete the selected expense:**")
        
        # Show expense details for confirmation
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid #ff6b6b;'>
            <h4>⚠️ Are you sure you want to delete this expense?</h4>
            <p><strong>Amount:</strong> ₹{selected_expense['amount']:.2f}</p>
            <p><strong>Description:</strong> {selected_expense['description']}</p>
            <p><strong>Paid by:</strong> {selected_expense['paid_by']}</p>
            <p><strong>Participants:</strong> {', '.join(selected_expense.get('participants', []))}</p>
            <p><strong>Split Type:</strong> {selected_expense.get('split_type', 'equal').title()}</p>
            {f"<p><strong>Group:</strong> {selected_expense.get('group', 'None')}</p>" if selected_expense.get('group') else ""}
            {f"<p><strong>Category:</strong> {selected_expense.get('category', 'None')}</p>" if selected_expense.get('category') else ""}
        </div>
        """, unsafe_allow_html=True)
        
        st.warning("⚠️ This action cannot be undone!")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Delete Expense", use_container_width=True, type="primary"):
                with st.spinner("Deleting expense..."):
                    response = make_api_request(f"/expenses/{selected_expense['id']}", method="DELETE")
                    
                    if response.get("success"):
                        st.success("✅ Expense deleted successfully!")
                        # Clear cache to refresh data
                        get_all_people.clear()
                        get_all_expenses.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete expense: {response.get('message', 'Unknown error')}")

def show_expense_history_tab():
    st.markdown("<div class='section-header'>Expense History</div>", unsafe_allow_html=True)
    
    with st.spinner("Loading expenses..."):
        expenses = get_all_expenses()
    
    if not expenses:
        st.info("📝 No expenses found. Add your first expense in the 'Add Expense' tab!")
        return
    
    # Filters
    groups = get_all_groups(expenses)
    all_people = sorted(set(
        p for exp in expenses 
        for p in ([exp['paid_by']] + exp.get('participants', []))
    ))
    categories = sorted(set(
        (exp.get('category') or 'Uncategorized')
        for exp in expenses
    ))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_group = st.selectbox("Filter by Group:", ["All"] + groups)
    with col2:
        selected_person = st.selectbox("Filter by Person:", ["All"] + all_people)
    with col3:
        selected_category = st.selectbox("Filter by Category:", ["All"] + categories)
    
    # Apply filters
    filtered_expenses = expenses
    
    if selected_group != "All":
        filtered_expenses = [e for e in filtered_expenses if e.get('group') == selected_group]
    
    if selected_person != "All":
        filtered_expenses = [
            e for e in filtered_expenses 
            if selected_person == e['paid_by'] or selected_person in e.get('participants', [])
        ]
    
    if selected_category != "All":
        filtered_expenses = [
            e for e in filtered_expenses 
            if e.get('category', 'Uncategorized') == selected_category
        ]
    
    st.markdown(f"<div style='margin-bottom:1em;'><b>{len(filtered_expenses)} of {len(expenses)} expenses shown</b></div>", unsafe_allow_html=True)
    
    # Display expenses
    for exp in filtered_expenses:
        participants_str = ', '.join(exp.get('participants', []))
        group_str = exp.get('group', 'No Group')
        category_str = exp.get('category', 'Uncategorized')
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                <div>
                    <h4 style='margin: 0 0 0.5em 0; color: #51cf66;'>₹{exp['amount']:.2f}</h4>
                    <p style='margin: 0 0 0.3em 0; font-size: 1.1em;'><strong>{exp['description']}</strong></p>
                    <p style='margin: 0; color: #999; font-size: 0.9em;'>
                        Paid by <strong>{exp['paid_by']}</strong> • {exp['split_type'].title()} split
                    </p>
                    <p style='margin: 0.3em 0 0 0; color: #999; font-size: 0.9em;'>
                        Group: {group_str} • Category: {category_str}
                    </p>
                    <p style='margin: 0.3em 0 0 0; color: #999; font-size: 0.9em;'>
                        Participants: {participants_str}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_dashboard_tab():
    st.markdown("<div class='section-header'>Dashboard</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Balances
    with col1:
        st.markdown("**💰 Balances**")
        with st.spinner("Loading balances..."):
            response = make_api_request("/balances")
        
        if response.get("success"):
            balances = response.get("data", [])
            if balances:
                df = pd.DataFrame(balances)
                # Format currency columns
                df['spent'] = df['spent'].apply(lambda x: f"₹{x:.2f}")
                df['owed'] = df['owed'].apply(lambda x: f"₹{x:.2f}")
                df['balance'] = df['balance'].apply(lambda x: f"₹{x:.2f}")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No balances to show. Add some expenses first!")
        else:
            st.error(f"Failed to load balances: {response.get('message')}")
    
    # Settlements
    with col2:
        st.markdown("**🔄 Settlement Suggestions**")
        with st.spinner("Calculating settlements..."):
            response = make_api_request("/settlements")
        
        if response.get("success"):
            settlements = response.get("data", [])
            if settlements:
                for s in settlements:
                    from_person = s.get('from') or s.get('from_')
                    to_person = s['to']
                    amount = s['amount']
                    st.info(f"💸 **{from_person}** pays **{to_person}**: ₹{amount:.2f}")
            else:
                st.success("🎉 All settled up! No payments needed.")
        else:
            st.error(f"Failed to load settlements: {response.get('message')}")
    
    st.divider()
    
    # System status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Check Database Health", use_container_width=True):
            with st.spinner("Checking..."):
                resp = make_api_request("/health")
                if resp.get("success") and resp.get("data", {}).get("status") == "healthy":
                    st.success("✅ Database is healthy")
                else:
                    st.error("❌ Database connection issues")
    
    with col2:
        docs_url = BACKEND_URL.replace("/api/v1", "/docs")
        if st.button("📚 View API Docs", use_container_width=True):
            st.markdown(f"[🔗 Open API Documentation]({docs_url})")
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            get_all_people.clear()
            get_all_expenses.clear()
            st.success("Data refreshed!")
            st.rerun()
    
    # App info
    st.markdown("""
    <div style='position:fixed; bottom:10px; right:10px; background:#23272b; border:1px solid #333; border-radius:8px; padding:0.7rem 1.2rem; font-size:0.95em; color:#f3f4f6; z-index:999;
        <b>🚀 SplitEase v1.0</b><br>
        Modern expense sharing made simple<br>
        <small>FastAPI + Streamlit + PostgreSQL</small><br>
        <i>Built with ❤️ for seamless expense splitting</i>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.markdown("<h1 style='text-align:center; font-size:2.5rem; margin-bottom:0.2em; color:#51cf66;'>💚 SplitEase</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#999; margin-bottom:2em; font-size:1.1em;'>Simple expense sharing for everyone</p>", unsafe_allow_html=True)
    
    # Initialize data on first load
    if not st.session_state.people_list:
        with st.spinner("Loading initial data..."):
            st.session_state.people_list = get_all_people()
            st.session_state.expenses_data = get_all_expenses()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "✏️ Edit/Delete", "📜 Expense History", "📊 Dashboard"])
    
    with tab1:
        show_add_expense_tab()
    
    with tab2:
        show_edit_delete_section()
    
    with tab3:
        show_expense_history_tab()
    
    with tab4:
        show_dashboard_tab()

if __name__ == "__main__":
    main()
