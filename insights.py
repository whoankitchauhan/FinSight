"""
insights.py — Derives plain-English spending insights from a filtered DataFrame.

Called by app.py after the user applies date/category filters on the Dashboard.
Returns a list of short strings that are rendered as the Smart Insights panel.
"""


def generate_insights(df):
    """
    Analyse a filtered expense DataFrame and return a list of insight strings.

    Insights cover:
    - Total spending in the selected period
    - The highest-spend category
    - Week-over-week trend (whether the latest week is up or down)
    - Whether any single transaction is unusually large (> 2× the average)
    """
    try:
        if df.empty:
            return ["No data available for the selected filters."]

        insights = []

        total = df["Amount"].sum()
        insights.append(f"Total spending in this period: ₹{total:,.2f}")

        category_totals = df.groupby("Category")["Amount"].sum()
        top_category = category_totals.idxmax()
        insights.append(f"Highest spending category: {top_category} (₹{category_totals[top_category]:,.2f})")

        # Week-over-week comparison using the two most recent full weeks
        df = df.copy()
        df["Week"] = df["Date"].dt.to_period("W")
        weekly = df.groupby("Week")["Amount"].sum()
        if len(weekly) >= 2:
            if weekly.iloc[-1] > weekly.iloc[-2]:
                insights.append("Spending went up compared to the previous week.")
            else:
                insights.append("Spending went down compared to the previous week.")

        # Flag transactions that are more than twice the average — likely one-offs
        avg = df["Amount"].mean()
        outliers = df[df["Amount"] > 2 * avg]
        if not outliers.empty:
            insights.append(
                f"You have {len(outliers)} unusually large transaction(s) "
                f"(more than 2× your ₹{avg:,.0f} average)."
            )

        return insights
    except Exception as e:
        print(f"Error generating insights: {e}")
        return ["Unable to generate insights at this time due to an error."]