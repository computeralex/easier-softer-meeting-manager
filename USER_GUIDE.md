# Easier Softer Meeting Manager — User Guide

Welcome to the **Easier Softer Meeting Manager**, a web application designed to help 12-step recovery groups manage their meetings, finances, contacts, literature, and more. This guide walks you through every feature available to you as a user.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [The Dashboard](#the-dashboard)
3. [Settings](#settings)
4. [User Management](#user-management)
5. [Service Positions](#service-positions)
6. [Meeting Format Builder](#meeting-format-builder)
7. [Readings Library](#readings-library)
8. [Phone List](#phone-list)
9. [Treasurer Tools](#treasurer-tools)
10. [Business Meetings](#business-meetings)
11. [Public Website](#public-website)
12. [Utilities (Backup & Restore)](#utilities-backup--restore)
13. [Your Profile & Password](#your-profile--password)
14. [Sharing & Public Access](#sharing--public-access)
15. [Permissions & Access Control](#permissions--access-control)

---

## Getting Started

### First-Time Setup Wizard

When you first log in after deployment, the setup wizard will walk you through the basics:

1. **Step 1 — Meeting Name:** Enter your meeting or group name.
2. **Step 2 — Service Positions:** Choose which default service positions to create for your group (Secretary, Treasurer, GSR, Literature Person, Greeter, Coffee Maker). You can always add or change positions later.

You can skip the wizard at any time:
- **Skip for Later** — the wizard will appear again next time you log in.
- **Skip Forever** — permanently dismisses the wizard.

### Logging In

Navigate to your site and click the login link. Enter your email address and password. If you forget your password, use the "Forgot Password" link on the login page to receive a reset email.

---

## The Dashboard

The dashboard is your home base after logging in. It displays module widgets based on your permissions — you will only see widgets for the modules you have access to. Each widget provides a quick summary and links to the full module.

Access the dashboard at any time by clicking **Dashboard** in the navigation.

---

## Settings

Access settings from the dashboard navigation. The settings page is organized into tabs.

### General Tab

Configure your meeting's core information:

| Setting | Description |
|---|---|
| **Meeting Name** | The name of your meeting or group |
| **Meeting Type** | Open, Closed, Speaker, Step Study, etc. |
| **Meeting Day & Time** | When your meeting takes place |
| **Meeting Timezone** | Your local timezone |
| **Meeting Address** | Physical location of the meeting |
| **Zoom ID & Password** | For online/hybrid meetings |
| **Group Service Number** | Your group's service number (e.g., GSO number) |
| **Sobriety Term** | Choose how your group refers to recovery time: Sobriety, Abstinence, Clean Time, Recovery, or a custom term |

### Appearance

- **Favicon** — Upload a small icon (32x32 or 64x64 PNG/ICO recommended) that appears in browser tabs.
- **Logo** — Upload a logo image (recommended max height: 200px) displayed on your site.

### Public Officers Display

Control how service position holders appear on your public site:

- **Not visible** — Officer information is hidden from the public site.
- **Positions and vacancy status only** — Shows position names and whether they are filled or open.
- **Positions + names** — Shows position names plus the first name and last initial of holders.

### Module Settings Tabs

Each active module (Treasurer, Phone List, Readings, Meeting Format, Website) adds its own settings tab. See the individual module sections below for details.

---

## User Management

If your position grants you user management permissions, you can manage the people in your group.

### Viewing Users

The user list shows all members with their current service positions and active/inactive status.

### Adding a New User

1. Go to **Users** and click **Add User**.
2. Enter the person's email address, first name, and last name.
3. Optionally assign a primary and/or secondary service position.
4. Save — the system will automatically send a welcome email with a link to set their password.
5. If email delivery fails, a temporary password will be shown on screen for you to share with them.

### Inviting Users

The invite flow is similar to adding a user but gives you additional options:

- **Placeholder users** — Create a user without an email address. Placeholder users can hold service positions and appear on lists but cannot log in. Useful for tracking who holds a position even if they don't need system access.
- **Send welcome email** — Toggle whether to email the new user or display a temporary password on screen instead.

### Editing a User

- Update name, email, phone number.
- Change service position assignments.
- Toggle a user between **active** and **inactive** (you cannot deactivate yourself).
- Send a password reset email on their behalf.

### Deleting a User

Delete a user with confirmation. This removes their account and any position assignments.

### Searching for Users

Use the search bar to quickly find users by name or email. Results appear instantly as you type.

---

## Service Positions

Service positions define the roles in your group (Secretary, Treasurer, GSR, etc.) and control what each person can access.

### Viewing Positions

The positions list shows all service positions with:
- Position name and description
- Current holder(s) and whether the position is filled or vacant
- Term status — how many days remain, or if the term is overdue

### Creating a Position

Click **Add Position** and fill in:

| Field | Description |
|---|---|
| **Name** | The position title (e.g., "Secretary") |
| **Description** | What the position is responsible for |
| **Default Term Length** | How many months a term lasts (default: 6 months) |
| **Sobriety Requirement** | Text describing the sobriety requirement (e.g., "1 year continuous sobriety") |
| **Duties** | Detailed list of responsibilities |
| **SOP** | Standard Operating Procedures for the position |

### Position Permissions

Each position can be granted specific access:

- **Can Manage Users** — Allows adding, editing, and removing users from the system.
- **Module Permissions** — Grant read-only or read/write access to individual modules (Treasurer, Phone List, Readings, Meeting Format, Business Meetings, Website).

### Assigning Users to Positions

1. Go to a position's detail page.
2. Click **Assign User** and select the person.
3. Choose **Primary** or **Secondary**:
   - **Primary** — This person is the official holder. When a primary holder is assigned, the position is marked as "filled."
   - **Secondary** — This person is helping out but the position still needs a dedicated holder.
4. Set the start date.

### Ending a Term

When someone's term is complete, click **End Term** on their assignment. This records an end date and frees the position for a new holder.

### Term Warnings

The system automatically tracks terms and shows warnings:
- **Ending soon** — The term will end within 30 days.
- **Overdue** — The term has passed its expected end date.

### Public Officer Directory

If enabled in settings, service position holders are listed on the public site so members and visitors can see who serves the group.

---

## Meeting Format Builder

The meeting format builder lets you create a customizable meeting script — the document that guides your meeting from start to finish.

### How It Works

Your meeting format is built from **blocks**. Each block is a section of the meeting (e.g., "Welcome," "Preamble," "Main Share," "Closing"). Blocks are displayed in order from top to bottom.

### Managing Blocks

- **Add a block** — Give it a title and optional description.
- **Reorder blocks** — Drag blocks up or down to change the meeting order.
- **Edit or delete blocks** — Modify the title/description or remove a block entirely.

### Variations

Each block can have multiple **variations** — different versions of the content that display based on meeting type or schedule.

For example, a "Main Content" block might have:
- A **Speaker** variation for speaker meetings
- A **Step Study** variation for step study meetings
- A **Default** variation shown when no specific type is selected

#### Creating a Variation

1. Go to a block and click **Add Variation**.
2. Enter the variation name and content using the rich text editor.
3. Optionally assign a **meeting type** (Speaker, Topic, Step Study, etc.).
4. Mark one variation as the **default** for when no specific type matches.

#### Embedding Readings

You can embed readings from your Readings Library directly into the meeting format using the reading's short name in square brackets:

```
[serenity_prayer]
```

When the format is displayed, the reading content will be substituted inline.

### Schedules

Variations can be shown on specific days or dates using **schedule rules**:

- **Specific date** — Show this variation only on a particular date (e.g., a group anniversary).
- **Day of week** — Show every Monday, every Friday, etc.
- **Occurrence** — Show on the 1st Tuesday, 3rd Saturday, etc. of each month.

This is useful for groups that rotate meeting types (e.g., speaker meeting on the first Saturday, step study on the third Saturday).

### Meeting Types

Create custom meeting types (Speaker, Topic Discussion, Step Study, Literature, etc.) to organize your variations. Meeting types can be:
- Reordered to control display priority
- Toggled active/inactive
- Edited or deleted

### Selecting Today's Meeting Type

The secretary (or whoever has format access) can select which meeting type to display on the public site. This changes which variations are shown to visitors viewing the format.

### Format Settings

In the Format settings tab:
- **Enable/disable public access** — Control whether the format is visible on the public site.
- **Editor font size** — Adjust the font size in the content editor (Small, Medium, Large, X-Large).
- **Display font size** — Adjust the font size on the public-facing format page.

---

## Readings Library

Store and organize your group's recovery literature, prayers, and readings in one place.

### Managing Readings

- **Add a reading** — Enter a title, select a category, and write or paste the content using the rich text editor.
- **Import from text** — Paste plain text and it will be automatically formatted into paragraphs.
- **Edit or delete readings** — Modify content or remove readings.
- **Short name** — Each reading gets a short name (slug) that can be used to embed it in the meeting format.

### Categories

Organize readings into categories (e.g., "Prayers," "Steps," "Traditions," "Group Readings"):
- Create, edit, and delete categories.
- Reorder categories with drag-and-drop.
- Reorder readings within each category.

### Readings Settings

In the Readings settings tab:
- **Enable/disable public access** — Control whether readings are visible on the public site.
- **Regenerate share token** — Create a new private share link (invalidates the old one).
- **Editor font size** — Adjust font size in the editor.
- **Display font size** — Adjust font size on the public readings page.

### Public Readings View

When enabled, visitors can browse readings organized by category with previous/next navigation and a position indicator (e.g., "3 of 25").

---

## Phone List

Manage your group's contact list and share it as a PDF or online link.

### Managing Contacts

- **Add a contact** — Enter name, phone number, email, time zone, and sobriety/recovery date.
- **Edit or delete contacts** — Update or remove contact information.
- **Reorder contacts** — Drag contacts to change the display order.
- **Toggle visibility** — Show or hide individual contacts from the public list.
- **Sponsor availability** — Mark contacts as available to sponsor.

### CSV Import

Import contacts from a spreadsheet using a 3-step wizard:

1. **Upload** — Select a CSV file from your computer.
2. **Map columns** — The system auto-detects column mappings, but you can adjust which CSV columns map to Name, Phone, Email, Time Zone, and Sobriety Date. Choose an import mode:
   - **Add only** — Only add new contacts.
   - **Update existing** — Update matching contacts and add new ones.
   - **Replace all** — Remove all existing contacts and replace with imported data.
3. **Preview & confirm** — Review the data and resolve any unknown time zones before completing the import.

### PDF Export

Generate a printable PDF of your phone list with customizable options:

| Option | Choices |
|---|---|
| **Layout** | Table or two-column list |
| **Font size** | 8pt to 12pt |
| **Show phone numbers** | Yes/No |
| **Show email addresses** | Yes/No |
| **Show time zones** | Yes/No |
| **Show sobriety dates** | Yes/No |
| **Footer text** | Custom text (default: privacy notice) |

### CSV Export

Export your contact list as a CSV file for use in spreadsheets.

### Phone List Settings

In the Phone List settings tab:
- **Enable/disable public access** — Control whether the phone list is visible on the public site.
- **Regenerate share token** — Create a new private share link.
- **Manage time zones** — Add or remove custom time zone options.

---

## Treasurer Tools

Track your group's finances with income and expense tracking, reports, and disbursement management.

### Initial Setup

When you first access the Treasurer module, the setup wizard will ask you to configure:
- **Prudent Reserve** — The amount your group keeps in reserve (e.g., 3 months of rent).
- **Starting Balance** — Your group's current bank balance.

### Recording Transactions

#### Adding Income
1. Click **Add Income**.
2. Enter the date, amount, description, and income category.
3. Optionally upload a receipt (JPG, PNG, or PDF).
4. Save.

#### Adding Expenses
1. Click **Add Expense**.
2. Enter the date, amount, description, and expense category.
3. Optionally upload a receipt.
4. If the expense is a disbursement, select a disbursement split to automatically divide the amount.
5. Save.

#### Viewing Transactions

Browse all transactions in a paginated table showing date, type (income/expense), description, category, and amount. Click any transaction to view details or edit it.

### Receipts

- Upload receipt files (JPG, PNG, PDF) when adding or editing transactions.
- View uploaded receipts from the transaction detail page.
- Receipts are stored securely and associated with their transaction.

### Categories

Manage how you classify income and expenses:

- **Income categories** — Default: "7th Tradition." Add categories like "Literature Sales," "Event Income," etc.
- **Expense categories** — Add categories like "Rent," "Literature," "Supplies," etc.
- **Default category** — Mark one category as the default for new transactions.
- **Disbursement category** — Mark expense categories that represent disbursements (e.g., donations sent to District, Area, or World Service).

### Disbursement Splits

Set up how your group divides disbursement funds:

1. **Create a split** — Give it a name (e.g., "Standard 60/30/10").
2. **Add split items** — Define each recipient and their percentage (e.g., 60% District, 30% Area, 10% GSO).
3. **Mark as default** — Set one split as the default for disbursement transactions.

When you record a disbursement expense and select a split, the system automatically calculates and creates individual line items for each recipient.

### Recurring Expenses

Set up expenses that repeat automatically:

1. Click **Add Recurring Expense**.
2. Enter the description, amount, category, and frequency (Weekly, Monthly, Quarterly, or Yearly).
3. Set the next due date.
4. The system will remind you or auto-generate the expense when it's due.

Recurring expenses can be toggled active/inactive at any time.

### Financial Reports

Generate periodic financial reports for your group:

1. Click **Create Report**.
2. The system suggests the next reporting period based on your last report.
3. The report shows:
   - **Date range** covered
   - **Total income** for the period
   - **Total expenses** for the period
   - **Net amount** (income minus expenses)
   - **Prudent reserve** amount
   - **Ending balance**
   - **Available balance** (ending balance minus prudent reserve)
4. Reports can be **archived** (locked from further changes).
5. Export reports as **PDF** or **CSV**.

### Year Summary

View an annual financial summary for GSR reports, showing totals grouped by year.

### Treasurer Settings

In the Treasurer settings tab:
- Update prudent reserve amount.
- Update starting balance.

---

## Business Meetings

Record and organize your group's business meeting minutes.

### Format Template

Set up a standard agenda template that serves as the starting point for each business meeting. Edit the template to include your group's standard agenda items (e.g., "Opening," "Treasurer Report," "Old Business," "New Business," "Closing").

### Recording a Business Meeting

1. Click **Add Business Meeting**.
2. Select the date (defaults to today).
3. Fill in agenda items, notes, attendance, decisions, and action items using the rich text editor.
4. Save.

### Viewing & Editing Meetings

- Browse all past business meetings in a list.
- Click any meeting to view the full minutes.
- Edit or delete meetings as needed.
- The system tracks who created and last updated each record.

---

## Public Website

Your group can have a public-facing website that visitors can access without logging in.

### Home Page

Choose what visitors see when they visit your site:
- **Meeting Format** — Display your meeting format as the home page.
- **CMS Page** — Display a custom page you've built.

### Module Visibility

Control which modules are accessible on the public site:

| Module | Default |
|---|---|
| Meeting Format | Visible |
| Readings | Visible |
| Phone List | Hidden |
| Treasurer Reports | Hidden |

### Navigation

The public navigation automatically includes links to enabled modules. Custom CMS pages can also be added to the navigation.

### CMS Pages

Create custom pages for your public site using the visual page editor:

1. Click **Add Page**.
2. Use the drag-and-drop visual editor to build your page content.
3. Set a page title, URL slug, and optional SEO fields (meta title, meta description, featured image).
4. Choose whether to show the page in the navigation menu.
5. Publish the page or save it as a draft.

CMS pages are accessible at `your-site.com/pages/your-page-slug/`.

### Login Link

Toggle whether a login link is visible on the public site navigation.

---

## Utilities (Backup & Restore)

Protect your group's data with the backup and restore tools, found under **Utilities** in the dashboard.

### Creating a Backup

Click **Download Backup** to generate a JSON file containing all your group's data (readings, format blocks, contacts, financial records, etc.).

Backups **do not** include user accounts, login sessions, or system configuration for security reasons.

### Restoring from a Backup

1. Click **Upload Backup**.
2. Select a previously downloaded JSON backup file.
3. Choose whether to **replace** existing data (clears current records before importing) or **merge** (adds to existing data).
4. Confirm to restore.

### Managing Backups

- View saved backups with filename, file size, and date.
- Download previous backups.
- Delete old backup files.

---

## Your Profile & Password

### Editing Your Profile

Click your name or **Profile** in the navigation to update:
- First name and last name
- Email address
- Phone number

### Changing Your Password

Go to **Password** in the navigation to change your password. You will need to enter your current password and then your new password twice to confirm.

### Resetting a Forgotten Password

From the login page, click **Forgot Password** and enter your email address. You will receive a link to set a new password.

---

## Sharing & Public Access

Several modules support sharing content with people who don't have accounts.

### Share Links

The Phone List, Readings, and Meeting Format modules each have a **share token** — a unique, private link you can send to members:

- **Phone List:** `your-site.com/p/TOKEN/`
- **Readings:** `your-site.com/r/TOKEN/`
- **Meeting Format:** `your-site.com/f/TOKEN/`

These links work even if the module is not enabled on the public site, making them useful for private sharing within your group.

### Regenerating Share Links

If you need to invalidate an old share link (e.g., for privacy), go to the module's settings and click **Regenerate Token**. This creates a new link and the old one will stop working.

### Public Site

When modules are enabled on the public site (via Website settings), anyone can access them without a share link or login — useful for groups that want open access to their format, readings, or other information.

---

## Permissions & Access Control

Access to features is controlled through **service positions**. Each position can be granted specific permissions.

### How Permissions Work

1. A position is created (e.g., "Secretary").
2. The position is granted permissions for specific modules (e.g., read/write access to Meeting Format and Readings).
3. A user is assigned to the position.
4. That user can now access and modify the modules their position allows.

### Permission Levels

For each module, a position can have:

- **No access** — The module is hidden from the user.
- **Read access** — The user can view but not edit.
- **Write access** — The user can view, create, edit, and delete.

### User Management Permission

The "Can Manage Users" permission is special — it allows a position holder to add, edit, and deactivate users. Typically only the Secretary or a similar administrative position would have this.

### Superuser Access

The account created during initial deployment is a superuser with full access to everything. Superuser status bypasses all permission checks.

---

## Tips & Best Practices

- **Start with the setup wizard** to get your meeting name and basic positions configured.
- **Assign positions before inviting users** so you can grant appropriate access right away.
- **Use placeholder users** for members who need to hold positions but don't need to log in.
- **Regenerate share tokens** periodically if membership changes and you want to control who has access.
- **Back up regularly** using the Utilities page, especially before making major changes.
- **Use the meeting format scheduler** if your group rotates meeting types — it automates which content displays on which days.
- **Embed readings in your format** using `[short_name]` syntax to keep your meeting script updated when readings change.
- **Set up recurring expenses** for regular costs like rent to save time on data entry.
- **Create disbursement splits** to automatically calculate how much goes to District, Area, and World Service.
- **Export financial reports** as PDF for group records or to share at business meetings.

---

## Getting Help

If you run into issues or have questions:

- Check the settings page for configuration options.
- Make sure your position has the necessary permissions for the feature you're trying to use.
- Contact your group's secretary or the person who set up the system for access changes.
- For technical issues with the software itself, visit the project's [GitHub repository](https://github.com/computeralex/easier-softer-meeting-manager).

---

*This guide covers Easier Softer Meeting Manager. For deployment and technical documentation, see the [README](README.md).*
