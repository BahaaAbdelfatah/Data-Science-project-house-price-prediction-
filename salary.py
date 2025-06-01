import streamlit as st

def calculate_salary(total_work_days, vacation_days_worked, vacation_days_taken):
    base_salary = 8000
    hourly_rate = 33.3333
    overtime_multiplier = 1.35
    overtime_threshold = 208
    bonus_per_12h_day = 50

    # Calculate hours
    normal_hours = total_work_days * 12
    vacation_work_hours = vacation_days_worked * 24
    vacation_off_hours = vacation_days_taken * 8

    base_counted_hours = normal_hours + vacation_off_hours
    overtime_hours = max(base_counted_hours - overtime_threshold, 0)
    overtime_pay = overtime_hours * hourly_rate * overtime_multiplier
    vacation_work_pay = vacation_work_hours * hourly_rate

    total_12h_days = total_work_days + vacation_days_worked
    bonus_12h_days = total_12h_days * bonus_per_12h_day
    days_off_bonus = 250 if vacation_days_taken < 2 else 200

    gross_salary = (
        base_salary +
        overtime_pay +
        vacation_work_pay +
        bonus_12h_days +
        days_off_bonus
    )

    net_salary = gross_salary * (1 - 0.17)

    return {
        "gross": round(gross_salary, 2),
        "net": round(net_salary, 2),
        "base_salary": base_salary,
        "overtime_pay": round(overtime_pay, 2),
        "vacation_work_pay": round(vacation_work_pay, 2),
        "bonus_12h_days": bonus_12h_days,
        "days_off_bonus": days_off_bonus,
        "overtime_hours": overtime_hours,
        "total_12h_days": total_12h_days
    }

# Streamlit UI
st.title("🧮 Salary Calculator (EGP)")
st.write("Welcome! This app calculates your monthly salary based on overtime, vacations, and bonuses.")

# Inputs
total_work_days = st.number_input("📅 Number of 12-hour Work Days", min_value=0, step=1)
vacation_days_worked = st.number_input("🏖️ Number of Vacation Days Worked (12h)", min_value=0, step=1)
vacation_days_taken = st.number_input("🛌 Number of Vacation Days Off", min_value=0, step=1)

if st.button("Calculate Salary 💵"):
    result = calculate_salary(total_work_days, vacation_days_worked, vacation_days_taken)

    st.subheader("📊 Salary Breakdown")
    st.write(f"**Base Salary (208h):** {result['base_salary']} EGP")
    st.write(f"**Overtime Hours:** {result['overtime_hours']}h → {result['overtime_pay']} EGP")
    st.write(f"**Vacation Days Worked Pay:** {result['vacation_work_pay']} EGP")
    st.write(f"**12h Day Bonus** ({result['total_12h_days']} days): {result['bonus_12h_days']} EGP")
    st.write(f"**Days-Off Bonus:** {result['days_off_bonus']} EGP")

    st.markdown("---")
    st.success(f"💰 **Gross Salary:** {result['gross']} EGP")
    st.error(f"📉 **Net Salary (after 17% deduction):** {result['net']} EGP")
