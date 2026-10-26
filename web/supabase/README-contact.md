# Contact form: how messages reach Outlook

The Contact page posts to the Supabase Edge Function `contact` (`supabase/contact/index.ts`). The function

1. refuses bots (a hidden field, a minimum fill time, a limit of 5 messages per visitor per hour and 300 a day),
2. keeps a copy of each message in the `contact_messages` table (no public access; only the function can write),
3. emails it to the team's mailbox through Microsoft Graph, so no outside form service sees the details.

The visitor's address is stored only as a salted hash. If Microsoft refuses the email, the message is still saved and
the reason is written to `email_error`, so nothing is lost and the cause can be found in the table.

## One-time setup

### Microsoft (Entra admin center, https://entra.microsoft.com, signed in as an administrator)
1. Identity > Applications > App registrations > New registration. Name: `Triada website contact form`. Account type:
   "Accounts in this organizational directory only". No redirect address. Register.
2. On the Overview page note the **Application (client) ID** and the **Directory (tenant) ID**. These are not secrets.
3. API permissions > Add a permission > Microsoft Graph > **Application permissions** > `Mail.Send` > Add, then
   **Grant admin consent**.
4. Certificates & secrets > New client secret (24 months). Copy the secret **Value** at once (shown only once) and
   put it straight into Supabase (below). Never put it in the website, an email or the repository.
   Set a calendar reminder to replace it before it expires.
5. Limit the app to one mailbox (Exchange Online PowerShell, as an administrator):
   ```
   Connect-ExchangeOnline
   New-DistributionGroup -Name "Website mail senders" -Type Security -Members hr@triadatechnologies.com
   New-ApplicationAccessPolicy -AppId <client id> -PolicyScopeGroupId "Website mail senders" -AccessRight RestrictAccess -Description "Contact form may send only as hr@"
   Test-ApplicationAccessPolicy -Identity hr@triadatechnologies.com -AppId <client id>     # AccessCheckResult: Granted
   Test-ApplicationAccessPolicy -Identity <any other mailbox> -AppId <client id>           # AccessCheckResult: Denied
   ```

### Supabase
1. SQL editor: run the `contact_messages` part at the end of `supabase/setup.sql`.
2. Edge Functions > create `contact`, paste `supabase/contact/index.ts`, Deploy with **Verify JWT off**.
3. Edge Functions > Secrets, add:
   `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MAIL_FROM` (`hr@triadatechnologies.com`),
   `MAIL_TO` (`hr@triadatechnologies.com`) and `IP_SALT` (any long random text).

## Checking it
Send a message from the Contact page. It should arrive in the mailbox within a minute, with Reply going to the
visitor. In Supabase > Table editor > `contact_messages`, the row shows `emailed = true`. A row with `emailed = false`
and text in `email_error` explains what to fix (a wrong secret, a missing permission, an expired secret).
