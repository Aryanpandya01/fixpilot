# BilliGo Cloud Billing & ERP

## System Overview
- **Application URL:** https://billigo.projectw.in/
- **Fastest navigation (direct page URLs):** open these with open_url instead of clicking menus:
  - Business profile: https://billigo.projectw.in/settings/business
  - Bank & UPI: https://billigo.projectw.in/settings/payment
  - Invoices & numbering: https://billigo.projectw.in/settings/numbering
  - Taxes & units: https://billigo.projectw.in/settings/taxes
  - Email (SMTP) settings: https://billigo.projectw.in/settings/email
  - Email templates: https://billigo.projectw.in/settings/email-templates
  - Email log: https://billigo.projectw.in/settings/email-log
  - Team members: https://billigo.projectw.in/settings/team
  - Roles & permissions: https://billigo.projectw.in/settings/roles
  - Audit log: https://billigo.projectw.in/settings/audit-log
  - Any other page: press `Ctrl+K` in BilliGo and type the page name (e.g. "Invoices").
- **Default Organization:** Shiv Enterprise (Bhavnagar)
- **Active Admin User:** Aryan Pandya (Admin)
- **Subscription Support:** support@projectw.in | +91 9376658932

---

## Screen Layout and Navigation

### 1. Global Navigation (Left Sidebar)
- **Top Organization Switcher:** Displays organization name (e.g., "Shiv Enterprise") and location ("Bhavnagar"). Clicking allows switching companies.
- **Search Bar:** "Search (Ctrl K)" — instant navigation to any module, invoice, or setting.
- **Main Modules (Top to Bottom):**
  - **Dashboard:** High-level summary of total sales, receivables, payables, and recent transactions.
  - **Sales:** Expandable dropdown containing:
    - *Invoices* (Tax invoices, GST bills)
    - *Estimates*
    - *Quotations*
    - *Proforma*
    - *Credit notes*
    - *Debit notes*
    - *Delivery challans*
  - **Purchases:** Vendor purchase orders, bills, and purchase returns.
  - **Customers:** Customer directory, contact details, outstanding balances, and ledger.
  - **Products & services:** Item catalog, inventory quantities, HSN codes, and pricing.
  - **Payments:** Recorded customer collections, payments received, and payment modes.
  - **Expenses:** Business operational expenses and categories.
  - **Reports:** GST GSTR-1 / GSTR-3B summaries, profit & loss, sales registers.
  - **Documents:** Uploaded business documents, attachments, and contracts.
- **Bottom Profile:** "Aryan Pandya (Admin)" with notifications bell badge.

### 2. Settings Submenu Structure
Clicking **Settings** opens a secondary menu grouped into five categories:
- **BUSINESS:**
  - `Business profile` (Legal business name, address, GSTIN, PAN, logo)
  - `Bank & UPI` (Bank account numbers, IFSC, UPI IDs, QR code for invoices)
- **BILLING:**
  - `Invoices & numbering` (Invoice prefixes, starting numbers, terms & conditions)
  - `Taxes & units` (GST tax slabs, HSN master, measurement units)
- **EMAIL:**
  - `Email (SMTP)`: **Custom domain email server configuration for invoices and receipts**
  - `Email templates`: Customizable email subject lines and body copy
  - `Email log`: History of all sent, delivered, and failed invoice emails
- **TEAM:**
  - `Team members`: Invite employees and staff
  - `Roles & permissions`: Role-based access control
  - `Audit log`: User activity and security audit trail
- **YOU:**
  - `Notifications`: Email and in-app alert preferences
  - `Account & security`: Admin credentials, 2-factor authentication

---

## How to: Configure Custom Private Domain Email (SMTP) & Send Test Mail

This is the primary automated support task when a customer asks:
- *"Customer wants to setup custom private domain email for sending invoices"*
- *"How to configure Hostinger SMTP for aryan@projectw.in?"*
- *"Custom email send using private domain email and send test mail"*

### Initial State
Initially, the SMTP settings page is clean and unconfigured, displaying an amber banner:
`Not tested yet — Test the connection before saving so invoices do not fail to send.`

### Step-by-Step Autonomous Action Flow:

1. **Navigate to SMTP Settings:**
   - In the left sidebar, click **Settings**.
   - Under the **EMAIL** section in the submenu, click **Email (SMTP)** (URL: `https://billigo.projectw.in/settings/email`).
   - Screen heading displays: `Email (SMTP)` with description:
     *"Invoices and receipts are sent from your own mailbox, so replies come to you. Use your provider's SMTP details; for Gmail or Microsoft 365 with 2-step verification, create an app password."*

2. **Select Provider (Hostinger / Private Domain):**
   - In the **Provider** card (*"Pick your provider to fill in the server, or enter it yourself"*):
   - Click the **Hostinger** button (pill).
   - This automatically populates:
     - `SMTP server`: `smtp.hostinger.com`
     - `Port`: `465`
     - `Encryption`: `SSL/TLS`

3. **Enter Server & Mailbox Credentials:**
   - In the **Server** card:
     - **SMTP server:** Verify or enter `smtp.hostinger.com`
     - **Port:** Verify or enter `465`
     - **Encryption:** Ensure **SSL/TLS** is selected (or click `SSL/TLS`)
     - **Username:** Enter the full mailbox address: `aryan@projectw.in`
     - **Password (Security & Privacy Guardrail):**
       - **Mode A (Recommended):** If no password is in the query, click the password input, then call `ask_user` with: *"Please type your email password in the highlighted box, then press Continue. FixPilot never reads or stores mailbox passwords."* After the customer presses Continue, go on with step 4. Never escalate for this.
       - **Mode B:** If customer explicitly passed the password in the query (e.g. `password: <pass>`), fill it into the password field.
       - **Mode C:** If the field displays `"Saved · leave blank to keep"`, leave it blank to keep the previously saved password.
     - *(Optional)* Click **Show** link next to Password if verification is needed.

4. **Configure Sender Information:**
   - In the **Sender** card:
     - **From name:** Enter `Shiv Enterprise` (matches active organization)
     - **From email:** Enter `aryan@projectw.in`
     - **Reply-to (optional):** Enter `aryan@projectw.in`

5. **Test Connection & Save Settings:**
   - Under the Sender card, click the button **Test connection** (with wrench 🔧 icon).
   - Wait for the connection verification result ("Connection successful").
   - Click the green button **Save settings**.
   - Confirmation badge appears confirming settings have been saved.

6. **Send Test Email & Activate Outgoing Emails:**
   - Scroll down to the **Test email and switch** card (*"Send a real message through the saved settings."*):
   - In the input field **Send a test email to**: enter `aryanpandya0505@gmail.com`
   - Click the button **Send test email** next to the input.
   - Ensure the toggle switch **Send emails from this account** is set to **ON** (green active state).
     *(Helper text: "Switch off to stop all outgoing invoice and receipt emails without deleting the settings.")*

---

## Alternative Providers Configuration Reference

### Google Workspace / Gmail
- Click **Google Workspace / Gmail** button.
- `SMTP server`: `smtp.gmail.com`
- `Port`: `587` (Encryption: `STARTTLS`) or `465` (`SSL/TLS`)
- `Username`: Your full Google email address
- `Password`: 16-character **Google App Password** (regular account password will fail with 2FA)

### Microsoft 365 / Outlook
- Click **Microsoft 365 / Outlook** button.
- `SMTP server`: `smtp.office365.com`
- `Port`: `587` (Encryption: `STARTTLS`)
- `Username`: Your Microsoft 365 email address
- `Password`: Microsoft App Password

### Zoho Mail (India)
- Click **Zoho Mail (India)** button.
- `SMTP server`: `smtp.zoho.in`
- `Port`: `465` (Encryption: `SSL/TLS`) or `587` (`STARTTLS`)

---

## How to: Add a Team Member

This task is invoked when a customer asks:
- *"Add team member: Rahul Sharma with email rahul@projectw.in and role Sales"*
- *"Customer wants to add Priya Patel, email: priya@gmail.com as Accountant"*
- *"Invite a new staff member to BilliGo"*

### Step-by-Step Autonomous Action Flow:
1. **Navigate to Team Members:**
   - In the left sidebar, click **Settings**.
   - Under the **TEAM** section in the submenu, click **Team members** (URL: `https://billigo.projectw.in/settings/team`).
   - The screen displays: `Team members` with description *"Everyone who can sign in to this business. What each person can do comes from their role."*

2. **Open the Add Member Modal:**
   - Click the top-right green button: **Add member**.
   - A modal titled **Add team member** opens.

3. **Fill Member Credentials:**
   - In field **Email**: enter the requested email address (e.g. `rahul@projectw.in`).
   - In field **Name**: enter the member's full name (e.g. `Rahul Sharma`).

4. **Select Role:**
   - Click the **Role** dropdown and select the specified role matching the query:
     - **Admin:** *Full access to this business, including team and settings. Cannot be edited.*
     - **Accountant:** *Payments, expenses and reports. Read-only on sales documents.*
     - **Manager:** *Runs day-to-day billing. Cannot change team or email settings.*
     - **Sales:** *Creates quotations and invoices for customers.*
     - **Staff:** *Creates draft invoices. Cannot finalize or see reports.*
   - *(Default to "Sales" or "Staff" if customer does not specify).*

5. **Submit & Confirm:**
   - Click the green button **Add member** inside the modal.
   - Modal closes and the new member is listed in the Team Members table with status **Active**.

---

## How to: Add Bank Account & UPI ID to Invoices

This task is invoked when a customer asks:
- *"Customer wants bank details and UPI on invoices: HDFC Bank, account holder Shiv Enterprise, account 50200012345678, IFSC HDFC0001926, branch Bhavnagar, UPI shiventerprise@hdfcbank"*
- *"Add my UPI ID so customers can pay by QR"* / *"Print my bank account on invoices"*

### Fast recipe (about 3 replies)
1. **Open the page:** call open_url with `https://billigo.projectw.in/settings/payment`.
   Heading: `Bank & UPI`, text: *"Printed in the payment section of invoices so customers know where to pay. Leave empty to hide."*
2. **Fill every field the customer gave, in ONE reply** (use the `type` action with the field's x/y, so it clicks the
   field and types in one action). The fields, top to bottom:
   - **Bank account** card (two columns):
     - Row 1: **Bank name** (left) · **Account holder name** (right)
     - Row 2: **Account number** (left) · **IFSC** (right)
     - Row 3: **Branch** (full width)
   - **UPI** card below it: **UPI ID** (left).
   - IMPORTANT: grey text inside empty fields ("HDFC Bank", "HDFC0001926", "business@hdfcbank") is only a
     placeholder hint, NOT a saved value. Type into those fields anyway.
   - Skip fields the customer did not give. Never invent an account number.
3. **Save:** as soon as a field changes, a dark bar appears at the bottom: *"You have unsaved changes"* with
   **Discard** and **Save changes**. Click **Save changes** (white button, right end of the bar). Never click Discard.
4. **Done looks like:** the dark bar disappears and the fields show the typed values in black text.
   learn_path: `Settings > Bank & UPI > Save changes`

---

## Other Common BilliGo How-To Workflows

### How to: Create a New Sales Invoice
1. In the left sidebar, click **Sales** -> **Invoices**.
2. Click the top-right button **+ New Invoice** (or press keyboard shortcut `F2`).
3. Select **Customer** from dropdown or click *+ Add new customer*.
4. Verify **Invoice Date**, **Due Date**, and **Invoice Number** (auto-generated).
5. In the Items table:
   - Select or type item name in **Products & services**.
   - Enter **Quantity**, **Rate (₹)**, and select **GST %** (0%, 5%, 12%, 18%, 28%).
6. Total tax (CGST + SGST or IGST) calculates automatically.
7. Click **Save & Send** (sends via configured private domain SMTP) or **Save & Print**.

### How to: Add a New Product or Service
1. In left sidebar, click **Products & services**.
2. Click **+ Add Product** button.
3. Fill required fields:
   - *Item Name:* (e.g., "Parle-G 100g")
   - *Item Type:* "Product" or "Service"
   - *HSN/SAC Code:* (e.g., 19053100)
   - *Sale Price:* ₹10
   - *Applicable GST Rate:* 18%
   - *Opening Stock:* (e.g., 100 Units)
4. Click **Save Product**.

### How to: Add a Customer
1. In left sidebar, click **Customers**.
2. Click **+ Add Customer**.
3. Fill *Customer Name*, *Mobile Number*, *Email*, *Billing Address*, and *GSTIN* (if B2B).
4. Click **Save Customer**.

---

## Common Errors and Fixes

- **"SMTP Authentication Failed (535 Incorrect authentication data)":**
  - Cause: Incorrect email password or username is not full email (`aryan@projectw.in`).
  - Fix: Verify password, ensure username includes full `@projectw.in` domain.
- **"Connection Timed Out (Port blocked)":**
  - Cause: Port 465 requires SSL/TLS; Port 587 requires STARTTLS. If network blocks port 465, switch to Port 587 with STARTTLS.
- **"Sender address rejected: not owned by user":**
  - Cause: The `From email` does not match the authenticated `Username`.
  - Fix: Ensure `From email` is identical to `Username` (`aryan@projectw.in`).
- **"Test email not received":**
  - Cause: Delay in delivery or placed in recipient's Spam folder.
  - Fix: Check Spam / Junk folder for `aryanpandya0505@gmail.com` and verify SPF/DKIM DNS records on domain `projectw.in`.

---

## Do NOT Do — Escalate to Human Support

- **Subscription Renewal:** Notice at top of screen *"Your Billigo subscription ends on 23 November 2026. To renew, contact Billigo support at support@projectw.in or +91 9376658932."* -> Escalate to human support immediately.
- **Deleting Data:** Bulk deletion of invoices, financial records, audit logs, or customer ledgers.
- **Master Security:** Modifying master admin email or transferring organization ownership.
