# Easier Softer Meeting Manager - User Guide

A complete guide to managing your 12-step recovery meeting group with Easier Softer Meeting Manager.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard](#dashboard)
3. [Meeting Format](#meeting-format)
4. [Readings Library](#readings-library)
5. [Phone List](#phone-list)
6. [Treasurer Tools](#treasurer-tools)
7. [Business Meetings](#business-meetings)
8. [Service Positions](#service-positions)
9. [User Management](#user-management)
10. [Public Website](#public-website)
11. [Settings](#settings)
12. [Utilities (Backup & Restore)](#utilities-backup--restore)
13. [Your Profile](#your-profile)

---

## Getting Started

### First Login

After your administrator creates your account (or you deploy your own instance), visit your site's URL and log in with your email and password. If you've forgotten your password, use the "Forgot Password" link on the login page to receive a reset email.

### Setup Wizard

The first time an administrator logs in, a setup wizard will guide you through two steps:

1. **Group Name** - Enter your meeting group's name (e.g., "Saturday Morning Group").
2. **Service Positions** - Select which service positions your group uses (Secretary, Treasurer, GSR, etc.). You can customize these later.

You can skip the wizard and configure everything later through Settings. The wizard won't appear again once completed or dismissed.

---

## Dashboard

The Dashboard is your home screen after logging in. It shows:

- **Welcome message** with your name
- **Widget cards** summarizing activity from modules you have access to (Treasurer balance, Phone List count, Readings count, etc.)
- **Quick Actions** - Shortcuts to common tasks based on your service position (e.g., "Add Transaction" and "View Reports" for Treasurers)

The sidebar on the left provides navigation to all areas of the app. On mobile devices, tap the **Menu** button to open the sidebar.

---

## Meeting Format

The Meeting Format Builder lets you create and customize your meeting's script - the document that the secretary or chairperson reads to run the meeting.

### Concepts

- **Blocks** - Sections of your meeting format (e.g., "Welcome," "Preamble," "Main Share," "Closing"). Each block has a title and an order.
- **Variations** - Different content versions within a block. This allows your meeting to have different scripts depending on the meeting type.
- **Meeting Types** - Labels like "Speaker," "Topic," "Literature," or "Step Study." When the secretary selects tonight's meeting type, the format automatically shows the correct variation for each block.
- **Schedules** - Optional rules that automatically select a variation based on the calendar (e.g., "1st Saturday = Speaker Meeting," "Every Tuesday = Step Study").

### How to Build Your Format

1. Navigate to **Meeting Format** from the sidebar.
2. Click **Add Block** to create a new section of your format.
3. Give the block a title (e.g., "Welcome") and save.
4. Within the block, click **Add Variation** to write the content for that section. The editor supports rich text formatting (bold, italic, lists, etc.).
5. If your meeting rotates formats, create a **Meeting Type** first (e.g., "Speaker," "Topic"), then assign variations to each type.
6. Set one variation as **Default** - this is shown when no specific meeting type is selected.
7. **Reorder blocks** by dragging them into the desired sequence.

### Meeting Type Selection

Before a meeting, the secretary can select tonight's meeting type. This causes the public format page to display the appropriate variation for each block.

### Embedding Readings

You can link to readings from the Readings Library directly in your format content using the syntax `[reading_slug]`. This pulls the reading content inline when displayed publicly.

### Public Sharing

The meeting format can be shared publicly via a unique link. Members can view it on their phones during the meeting. You can also print a formatted version. Public access can be enabled or disabled in Settings.

### Settings

- **Public access** - Enable/disable the public format link
- **Font sizes** - Adjust editor and display font sizes (Small, Medium, Large, Extra Large)
- **Share link** - Regenerate the public URL token if needed

---

## Readings Library

Store and organize all of your group's recovery literature, prayers, and readings.

### Managing Readings

1. Navigate to **Readings** from the sidebar.
2. Click **Add Reading** to create a new reading.
3. Fill in the details:
   - **Title** - The reading's name (e.g., "Serenity Prayer," "How It Works")
   - **Short Name** - A brief label for use in meeting format links
   - **Content** - The full text of the reading, with rich text formatting
   - **Category** - Assign to a category for organization
   - **Copyright Notice** - Source attribution displayed at the bottom of the reading
   - **Notes** - Internal notes (not shown publicly)
   - **No-Index** - Optionally prevent search engines from indexing copyrighted material

### Categories

Organize readings into categories like "Prayers," "Steps," "Traditions," or "Literature":

1. Go to **Readings > Categories**.
2. Click **Add Category** and give it a name.
3. Drag categories to reorder them.

### Reordering

Use the **Reorder** page to drag and drop both categories and individual readings within categories into your preferred order.

### Importing Readings

You can import readings from a shared source:

1. Go to **Readings > Import**.
2. Follow the prompts to import pre-built reading sets.

### Public Access

Readings can be shared publicly. Each reading gets its own page with formatted content and optional copyright notices. Public access is toggled in Settings.

### Settings

- **Public access** - Enable/disable public viewing
- **Show sources** - Toggle source citations on public pages
- **Font sizes** - Adjust editor and display font sizes
- **Share link** - Regenerate the public URL token

---

## Phone List

Manage your meeting's member contact list with export and sharing options.

### Managing Contacts

1. Navigate to **Phone List** from the sidebar.
2. Click **Add Contact** to create a new entry.
3. Fill in the contact details:
   - **Name** - The member's name
   - **Phone** - Phone number
   - **WhatsApp** - Check if this number is on WhatsApp
   - **Email** - Email address
   - **Available to Sponsor** - Mark if this member is available to sponsor
   - **Sobriety Date** - The member's sobriety/clean date
   - **Time Zone** - Select from available time zones
   - **Notes** - Private notes about this contact
   - **Active** - Toggle whether this contact appears on the public list

### Toggle Visibility

Quickly toggle a contact's visibility (active/inactive) directly from the list without editing.

### Importing Contacts

Import contacts in bulk from a CSV file:

1. Go to **Phone List > Import**.
2. Upload your CSV file.
3. **Map columns** - Match your CSV columns to the contact fields (name, phone, email, etc.).
4. **Review and confirm** the import before it's processed.

### Exporting

- **PDF Export** - Generate a formatted PDF of your phone list, suitable for printing or sharing. Customize layout, font size, and which fields to include.
- **CSV Export** - Download your contacts as a CSV file for use in spreadsheets or other tools.

### PDF Settings

Customize your PDF phone list output:

- **Layout** - Choose between Table or Two-Column List format
- **Font size** - From 8pt (very compact) to 12pt (extra large)
- **Visible fields** - Toggle Phone/WhatsApp, Email, Time Zone, and Sobriety Date columns
- **Footer text** - Custom privacy reminder at the bottom of the PDF

### Public Access

The phone list can optionally be shared via a public link. This is disabled by default for privacy. Enable it in Settings if your group wants online access to the phone list.

### Settings

- **Public access** - Enable/disable the public phone list link
- **Time zones** - Add or remove time zone options for contacts
- **PDF settings** - Configure export layout and field visibility
- **Share link** - Regenerate the public URL token

---

## Treasurer Tools

Complete financial management for your group's treasury, including income/expense tracking, reporting, and disbursement calculations.

### Initial Setup

Before using the Treasurer tools, complete the setup:

1. Navigate to **Treasury** from the sidebar.
2. If prompted, click **Complete Setup**.
3. Enter your **Starting Balance** (current amount in the group's account).
4. Set your **Prudent Reserve** (the amount your group keeps in reserve for emergencies).

### Dashboard

The Treasurer Dashboard shows at a glance:

- **Available Funds** - Current balance minus the prudent reserve
- **Total Income** / **Total Expenses** / **Current Balance** / **Prudent Reserve**
- **Recent Transactions** - The latest income and expense entries
- **Quick Actions** - Links to Create Report, Settings, Recurring Expenses, and Year Summary

### Adding Transactions

1. Click **Add Transaction** from the dashboard or sidebar.
2. Select the type: **Income** or **Expense**.
3. Enter the date, amount, and description.
4. Choose a category:
   - For income: Select an income category (default is "7th Tradition")
   - For expenses: Select an expense category, or a disbursement category to trigger split calculations
5. Optionally attach a **receipt** (image or PDF).
6. Add any notes and save.

### Transaction List

View all transactions with filtering and search. Click any transaction to see its details, edit, or delete it.

### Expense Categories

Set up categories to organize your expenses:

- **Regular categories** - Rent, Literature, Supplies, etc.
- **Disbursement categories** - For contributions to District, Area, or World Service (triggers automatic split calculations)

### Income Categories

Categorize income sources (default: "7th Tradition"). Add custom categories like "Literature Sales" or "Bank Interest."

### Disbursement Splits

Configure how your group divides contributions:

1. Go to **Treasurer Settings > Splits**.
2. Create a split configuration (e.g., "Standard Split").
3. Add items with percentages (e.g., District 60%, Area 30%, World Service 10%).
4. When recording a disbursement expense, the app automatically calculates how much goes to each entity.

### Recurring Expenses

Set up recurring expenses that repeat on a schedule:

- **Frequency** - Weekly, Monthly, Quarterly, or Yearly
- **Amount and Category** - Pre-filled for convenience
- **Next Due Date** - Tracks when the expense is next due

### Reports

Generate financial reports for business meetings:

1. Click **Create Report**.
2. Select the **date range** for the report period.
3. The report automatically calculates totals for income, expenses, net amount, ending balance, and available balance.
4. **Export** reports as PDF or CSV for printing or sharing.
5. **Archive** completed reports to lock them.

### Year Summary

View an annual overview of all financial activity, broken down by month, with yearly totals.

---

## Business Meetings

Record and manage your group's business meeting minutes.

### Format Template

Create a reusable template/script for how your business meetings are run:

1. Navigate to **Business Meetings > Format**.
2. Edit the template using the rich text editor. A default template is provided with sections for Opening, Officer Reports, Old Business, New Business, and Closing.
3. Customize it to match your group's procedures.

### Recording Meeting Minutes

1. Navigate to **Business Meetings** from the sidebar.
2. Click **New Meeting**.
3. Enter the **date** of the business meeting.
4. Use the rich text editor to record **notes and minutes** - motions, votes, discussions, action items, etc.
5. Save the meeting record.

### Meeting History

Browse all past business meetings in chronological order. Click any meeting to view its full minutes, edit them, or delete the record.

---

## Service Positions

Manage your group's service positions and track who holds each role.

### Viewing Positions

Navigate to **Service Positions** from the sidebar (or via **Users > Service Positions**) to see all positions, who currently holds them, and their term status.

### Creating Positions

1. Click **Add Position**.
2. Fill in the details:
   - **Display Name** - The position title (e.g., "Literature Chair")
   - **Description** - What the position entails
   - **Term Length** - Default term in months (e.g., 6 months)
   - **Sobriety Requirement** - Suggested sobriety requirement (e.g., "1 year continuous")
   - **Duties** - Detailed list of responsibilities
   - **Standard Operating Procedures** - Step-by-step procedures for the role
   - **Show on Public Site** - Whether to display this position on the public officers page
   - **Warn on Multiple Holders** - Alert when more than one person holds this position

### Assigning Positions

1. Click on a position, then click **Assign**.
2. Search for an existing user or create a new one.
3. Set the **start date** for the assignment.
4. Choose whether this is a **Primary** or **Secondary** assignment:
   - **Primary** - This person's main responsibility. The position is considered "filled."
   - **Secondary** - This person is covering the role in addition to their primary position. The position is still considered "available" (needs a dedicated holder).

### Term Tracking

- Each assignment tracks its **start date** and calculates an **expected end date** based on the position's term length.
- Positions are flagged when terms are **ending soon** (within 30 days) or **overdue** (past the expected end date).
- When a term ends, click **End Term** and set the end date. The assignment moves to history.

### Position Permissions

Each position can be configured with module-level permissions:

- **Module Access** - Grant read or write access to specific modules (Treasurer, Phone List, Readings, etc.)
- **User Management** - Allow this position to add, edit, and remove users

### Position History

View the full history of who has held each position, including past assignments with their start and end dates.

---

## User Management

Manage who has access to the system. Available to administrators and users with positions that have user management permissions.

### User List

Navigate to **Users** from the sidebar to see all users, their positions, and their active/inactive status.

### Adding Users

1. Click **Add User**.
2. Enter their **email**, **first name**, **last name**, and **phone number**.
3. Set a temporary password or leave it blank.
4. The user can log in and change their password.

### Inviting Users

1. Click **Invite User**.
2. Enter the person's email address.
3. They will receive an email with login credentials.

### Placeholder Users

Users can be created without an email address. These "placeholder" users:

- Can hold service positions and appear in position tracking
- Cannot log in to the system
- Are useful for tracking who holds a position even if they don't need system access

### Managing Users

- **Edit** - Update a user's name, email, or other details
- **Activate/Deactivate** - Toggle a user's active status (deactivated users cannot log in)
- **Send Password Reset** - Send a password reset email to a user
- **Delete** - Permanently remove a user from the system

---

## Public Website

Your group can have a public-facing website that members and newcomers can access without logging in.

### What's on the Public Site

Depending on your settings, the public site can include:

- **Meeting Format** - Tonight's meeting script, viewable on phones during the meeting
- **Readings** - Browse all readings and prayers
- **Phone List** - Member contact list (disabled by default for privacy)
- **Service Positions** - Current officers and open positions
- **Treasurer Reports** - Published financial reports
- **Custom CMS Pages** - Create custom pages like "About Us," "Meeting Schedule," or "Newcomers"

### CMS Pages

Create custom web pages using the built-in page editor:

1. Navigate to **Website** admin from the dashboard.
2. Click **Add Page**.
3. Enter a **title** and **slug** (URL path).
4. Use the visual editor to build your page content.
5. Configure SEO fields (meta title, meta description) if desired.
6. Choose whether to **show in navigation** and set the **nav order**.
7. Publish or save as draft.

### Website Settings

Control what appears on the public site:

- **Home Page** - Choose whether the home page shows the Meeting Format or a CMS Page
- **Module Visibility** - Toggle which modules appear in public navigation (Format, Readings, Phone List, Treasurer)
- **Login Link** - Show or hide the login link in public navigation
- **Service Position Display** - Choose how service positions appear publicly:
  - **Hidden** - Not visible
  - **Positions Only** - Show positions and vacancy status
  - **Names** - Show positions with officer first name and last initial

### Branding

- **Logo** - Upload a logo for the website header (recommended: max 200px height)
- **Favicon** - Upload a custom favicon (recommended: 32x32 or 64x64 PNG/ICO)

---

## Settings

Access Settings from the sidebar. Settings are organized into tabs.

### General Tab

Configure your group's core information:

- **Meeting Name** - Your group's name (shown in the header and on the public site)
- **Meeting Type** - The type of meeting (e.g., Open, Closed, Speaker, Step Study)
- **Meeting Day and Time** - When your meeting occurs
- **Meeting Timezone** - Your local timezone
- **Meeting Address** - Physical or virtual meeting location
- **Zoom ID / Password** - For virtual or hybrid meetings
- **Group Service Number** - Your group's GSO service number
- **Sobriety Term** - Choose the term your fellowship uses (Sobriety, Abstinence, Clean Time, Recovery, or a custom term)
- **Logo and Favicon** - Upload custom branding images

### Module Tabs

Each module (Meeting Format, Readings, Phone List, Treasurer, Service Positions) has its own settings tab with module-specific configuration options. See individual module sections above for details.

---

## Utilities (Backup & Restore)

Available to administrators only, accessible from the sidebar under **Utilities**.

### Backup

Download a complete backup of all your data as a JSON file. This includes:

- Users and positions
- Transactions and financial records
- Readings and meeting format
- Phone list contacts
- Settings and configuration

Backups contain sensitive data (including password hashes), so store them securely.

### Restore

Restore data from a previously downloaded backup file:

1. Click **Choose File** and select your backup JSON.
2. Optionally check **Replace existing data** to clear current data before restoring (this deletes existing positions, transactions, and other data first).
3. Click **Restore Backup**.

**Important:** Users are never restored from backups for security reasons. Only data like positions, transactions, readings, and settings are restored.

### Server Backups

If server-side backups exist, they appear in a table with options to download or delete them.

---

## Your Profile

Access your profile from the sidebar by clicking your email address.

### Profile Information

Update your personal details:

- First name
- Last name
- Phone number

### Change Password

Click **Change Password** from your profile page to update your login password.

### Password Reset

If you've forgotten your password, use the **Forgot Password** link on the login page. You'll receive an email with a link to create a new password.

---

## Tips for Getting Started

1. **Complete the Setup Wizard** - Set your group name and select service positions.
2. **Add your readings** - Import or manually add the prayers and readings your meeting uses.
3. **Build your meeting format** - Create blocks for each section of your meeting and write the content.
4. **Set up the phone list** - Add member contacts or import from a CSV file.
5. **Configure the treasurer** - Set your starting balance and prudent reserve, then start recording transactions.
6. **Invite other trusted servants** - Add users and assign them to their service positions so they can access the tools they need.
7. **Share the public site** - Send your group's URL to members so they can access the meeting format, readings, and phone list from their devices.

---

## Need Help?

- Report issues or request features at: https://github.com/computeralex/easier-softer-meeting-manager/issues
- For the hosted version, visit: [recoverymeeting.app](https://recoverymeeting.app)
