export const HOSTED_API_BASE = 'https://gds-pmoh-demo-be-wa-eus.azurewebsites.net'

export const DEMO_LOGIN = {
  email: 'Admin123@ey.com',
  password: 'Admin123@ey.com',
  stay_signed_in: false,
}

export const AGENTS = [
  {
    id: 'brd',
    number: 1,
    title: 'BRD Agent',
    endpoint: '/v1/brd/preview',
    summary: 'Creates or normalizes the source Business Requirements Document.',
    input: 'Uploaded PDF/Word file or default source brief',
    after: 'source intake',
  },
  {
    id: 'stories',
    number: 2,
    title: 'User Story Agent',
    endpoint: '/v1/userstory/generate-file',
    summary: 'Transforms the BRD into backlog, epics, and acceptance criteria.',
    input: 'BRD Word document from BRD Agent',
    after: 'BRD Agent',
  },
  {
    id: 'planner',
    number: 3,
    title: 'Planner Agent',
    endpoint: '/planer/upload',
    summary: 'Builds WBS, schedule, sprint plan, milestones, dependencies, risks, and quality audit.',
    input: 'BRD Word document from BRD Agent',
    after: 'BRD Agent',
  },
  {
    id: 'budget',
    number: 4,
    title: 'Budget Agent',
    endpoint: '/v1/budget/generate-from-file',
    summary: 'Builds cost and financial planning from the planner output.',
    input: 'Planner Word document from Planner Agent',
    after: 'Planner Agent',
  },
  {
    id: 'executive',
    number: 5,
    title: 'Executive Report Agent',
    endpoint: '/v1/executive-report/generate',
    summary: 'Combines all generated documents into an executive report.',
    input: 'BRD, user-story, planner, and budget Word documents',
    after: 'Budget Agent',
  },
]

export const DEFAULT_SOURCE = {
  project_name: 'Restaurant Web App',
  demand_id: 'REST-WEB-001',
  purpose:
    'Create a restaurant web application for menu browsing, online ordering, delivery or pickup checkout, table reservations, promotions, notifications, and staff order management.',
  stakeholders: [
    'Restaurant Owner as executive sponsor',
    'Operations Manager as business requester',
    'Restaurant Staff as order and reservation operators',
    'Customers as end users',
    'Digital Delivery Team as implementation owner',
  ],
  scope: [
    'Menu browsing with categories, images, prices, allergens, and preparation times',
    'Search and filters for vegetarian, vegan, spicy, gluten-free, and price range',
    'Cart and checkout for pickup and delivery orders',
    'Table reservation request and confirmation',
    'Admin dashboard for menu, promotions, orders, and reservations',
    'Order status tracking and customer notifications',
  ],
  functional_requirements: [
    'Customers can browse menu categories and view item details.',
    'Customers can search and filter menu items.',
    'Customers can add items to cart and edit quantities.',
    'Customers can submit pickup or delivery orders.',
    'Customers can request table reservations.',
    'Staff can accept, prepare, dispatch, and complete orders.',
    'Managers can update menu item availability, prices, and promotions.',
  ],
  non_functional_requirements: [
    'The application must be responsive across desktop, tablet, and mobile browsers.',
    'Customer login and order information must be protected.',
    'The home page should load within 3 seconds on normal broadband.',
    'The system should handle 200 concurrent users during peak hours.',
  ],
  dependencies: [
    'Payment gateway integration',
    'Email or SMS notification service',
    'Restaurant operating hours and table availability data',
    'Authentication service',
  ],
  risks: [
    'Order status delays could reduce customer trust.',
    'Incomplete menu data could block launch readiness.',
    'Payment integration delays could affect checkout scope.',
  ],
}
