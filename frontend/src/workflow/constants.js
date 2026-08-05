export const HOSTED_API_BASE = 'https://gds-pmoh-demo-be-wa-eus.azurewebsites.net'

export const DEMO_LOGIN = {
  email: 'Admin123@ey.com',
  password: 'Admin123@ey.com',
  stay_signed_in: false,
}

export const DEFAULT_BRIEF = {
  project_name: 'Restaurant Web App',
  document_purpose:
    'This BRD defines the requirements for a restaurant web application that allows customers to browse the menu, place pickup or delivery orders, reserve tables, and receive order updates.',
  business_objective:
    'The restaurant wants a single web application to reduce phone orders, improve online ordering, and give customers a simple way to view menu items, promotions, and reservation availability.',
  target_users: ['Customers', 'Restaurant staff', 'Restaurant managers', 'Customer support team'],
  in_scope: [
    'Public menu browsing',
    'Search and filter menu items by category, dietary preference, and price',
    'Customer sign-up and login',
    'Shopping cart and checkout for pickup and delivery orders',
    'Table reservation request and confirmation',
    'Order status tracking',
    'Promotions and coupon code support',
    'Admin panel for menu and order management',
  ],
  out_of_scope: [
    'Native mobile app',
    'Multi-restaurant marketplace support',
    'Third-party loyalty program integration in the first release',
    'Dine-in POS replacement',
  ],
  functional_requirements: [
    'The application shall display the restaurant name, location, opening hours, and featured offers on the home page.',
    'The application shall allow customers to browse menu categories such as starters, mains, desserts, drinks, and specials.',
    'The application shall allow customers to search menu items by name and filter by vegetarian, vegan, spicy, gluten-free, and price range.',
    'The application shall show each menu item with image, description, price, allergens, and estimated preparation time.',
    'The application shall allow customers to add menu items to a cart and update quantities before checkout.',
    'The application shall support guest checkout and registered customer checkout.',
    'The application shall capture delivery address, contact number, and delivery instructions for delivery orders.',
    'The application shall allow customers to choose pickup time or delivery slot during checkout.',
    'The application shall support table reservation requests with date, time, party size, and special requests.',
    'The application shall send confirmation messages for successful orders and reservations.',
    'The application shall show real-time order status updates such as received, preparing, ready, out for delivery, and completed.',
    'The application shall allow customers to apply coupon codes during checkout.',
    'The application shall allow managers to update menu items, prices, availability, and promotions from an admin dashboard.',
    'The application shall allow restaurant staff to view incoming orders and reservation requests.',
    'The application shall allow staff to mark orders as accepted, preparing, ready, dispatched, or completed.',
  ],
  non_functional_requirements: [
    'The application shall load the home page within 3 seconds on a normal broadband connection.',
    'The application shall be responsive for desktop, tablet, and mobile browsers.',
    'The application shall protect customer login and order information.',
    'The application shall handle at least 200 concurrent users during peak hours.',
    'The application shall support audit logging for order and menu changes.',
  ],
  business_rules: [
    'Pickup orders can only be scheduled during restaurant opening hours.',
    'Delivery slots depend on delivery zone and kitchen capacity.',
    'Table reservations require confirmation before they are final.',
    'Coupon codes may be restricted by order value or date range.',
  ],
  assumptions: [
    'The restaurant already has menu data available in a spreadsheet or CMS.',
    'Payment will be handled through an existing payment gateway.',
    'Staff will use the admin dashboard from a browser.',
  ],
  dependencies: [
    'Email or SMS notification service',
    'Payment gateway integration',
    'Authentication service',
    'Restaurant operating hours and table availability data',
  ],
  acceptance_criteria_expectations: [
    'Customers can complete an order end to end from menu browse to confirmation.',
    'Customers can submit a reservation request and receive a confirmation.',
    'Staff can view and update order status from the admin dashboard.',
    'Managers can update menu items without developer support.',
    'The system clearly handles missing menu availability or invalid coupon codes.',
  ],
  demand_id: 'REST-WEB-001',
  affected_business_unit: 'Restaurant Operations',
  sponsor: 'Restaurant Owner',
  it_owner: 'Digital Delivery Team',
  requester_name: 'Operations Manager',
  classification: 'Internal',
  issue_date: '2026-08-06',
  business_rationale:
    'Reduce manual phone orders, improve order accuracy, increase customer convenience, and provide staff with a single digital workflow for menu, order, and reservation management.',
  scope:
    'Build a restaurant web application covering menu browsing, filtering, ordering, pickup and delivery checkout, table reservations, customer notifications, order tracking, and restaurant admin workflows.',
  expected_outcome:
    'Generate a BRD, user-story backlog, planner report, budget plan, and executive report for restaurant web app delivery planning.',
}

export const AGENT_STEPS = [
  {
    id: 'brd',
    title: 'BRD Agent',
    summary: 'Creates or normalizes the source business requirements document.',
    input: 'Uploaded BRD or default project brief',
    output: 'BRD document',
  },
  {
    id: 'userStories',
    title: 'User Story Agent',
    summary: 'Transforms the BRD into product backlog and acceptance criteria.',
    input: 'BRD document',
    output: 'User-story document',
  },
  {
    id: 'planner',
    title: 'Planner Agent',
    summary: 'Builds WBS, schedule, sprint plan, milestones, dependencies, risks, and quality audit.',
    input: 'BRD document',
    output: 'Planner document',
  },
  {
    id: 'budget',
    title: 'Budget Agent',
    summary: 'Estimates cost and financial planning based on planner output.',
    input: 'Planner document',
    output: 'Budget document',
  },
  {
    id: 'executive',
    title: 'Executive Report Agent',
    summary: 'Combines the produced documents into leadership-ready reporting.',
    input: 'BRD, stories, planner, and budget documents',
    output: 'Executive report',
  },
]
