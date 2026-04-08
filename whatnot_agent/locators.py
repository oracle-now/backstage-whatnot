LOGIN_MARKERS = [
    "[data-testid='avatar']",
    "[data-testid='profile-menu']",
    "button[aria-label*='account' i]",
    "button[aria-label*='profile' i]",
    "text=Seller Hub",
    "text=Inventory",
    "text=Payouts",
    "text=Your shows",
]

ORDERS_ROOTS = [
    "[data-testid='orders-table']",
    "[data-testid='sold-orders']",
    "table",
    "[role='table']",
]

ORDER_ROWS = [
    "[data-testid='orders-table'] tbody tr",
    "[data-testid='sold-orders'] [role='row']",
    "table tbody tr",
    "[role='rowgroup'] [role='row']",
    "[data-testid*='order' i] [role='row']",
    "[class*='order' i] table tbody tr",
    "[class*='order' i] [class*='row' i]",
    "article[class*='order' i]",
    "div[data-testid*='order' i]",
]

NEXT_PAGE = [
    "button[aria-label*='next']",
    "button:has-text('Next')",
    "[data-testid='pagination-next']",
    "a[rel='next']",
]
