# EDIT BUTTON
if cols[5].button("✏️", key=f"edit{row['id']}"):
    st.session_state.edit_id = row["id"]

# SHOW EDIT FORM (OUTSIDE BUTTON)
if st.session_state.get("edit_id") == row["id"]:
    st.markdown("---")
    st.subheader("Edit Expense")

    new_date = st.date_input("Date", pd.to_datetime(row["date"]), key=f"date_{row['id']}")
    new_item = st.text_input("Item", row["item"], key=f"item_{row['id']}")
    new_category = st.text_input("Category", row["category"], key=f"cat_{row['id']}")
    new_amount = st.number_input("Amount", value=float(row["amount"]), key=f"amt_{row['id']}")

    colA, colB = st.columns(2)

    with colA:
        if st.button("💾 Save", key=f"save_{row['id']}"):
            update_expense(
                row["id"],
                st.session_state.user,
                str(new_date),
                new_item,
                new_category,
                new_amount
            )
            st.success("Updated!")
            st.session_state.edit_id = None
            st.rerun()

    with colB:
        if st.button("❌ Cancel", key=f"cancel_{row['id']}"):
            st.session_state.edit_id = None
            st.rerun()
