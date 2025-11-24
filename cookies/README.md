# 🍪 Cookies Directory

This directory stores authenticated session cookies for WebMirror.

## What Are These Files?

When you log in to a website using WebMirror's Authentication Manager, your session cookies are saved here as JSON files. These cookies allow WebMirror to access the site as if you're logged in, without requiring you to log in again each time.

## File Format

Each file is named `[session_name].json` and contains:
- Cookie name and value
- Domain and path
- Expiry date
- Security flags

## Security Important! 🔒

### DO NOT:
- ❌ Share these files with anyone
- ❌ Commit them to git (already gitignored)
- ❌ Upload them to public servers
- ❌ Email or message them

### Why?
These files contain **authentication tokens** that give access to your accounts. Sharing them is like sharing your password!

## Managing Cookies

### View Saved Sessions

Check this directory or use the GUI's "Load Cookies" tab.

### Delete Old Sessions

Simply delete the JSON file:
```bash
rm ./cookies/old_session.json
```

### Refresh Expired Sessions

If a site logs you out:
1. Delete the old cookie file
2. Use Authentication Manager to log in again
3. Save a new session

## Cookie Expiry

Session cookies expire based on the website's policy:
- **Google**: Usually 1-2 weeks
- **Facebook**: Usually 30 days
- **LinkedIn**: Usually 7 days
- **GitHub**: Usually 30 days

Signs your cookies expired:
- Site shows login page
- "Authentication failed" errors
- WebMirror can't access protected content

## Best Practices

1. **Use Descriptive Names**
   - ✅ `google_work_account.json`
   - ✅ `facebook_personal.json`
   - ❌ `session1.json`

2. **Separate Work and Personal**
   - Keep different accounts in different files
   - Use appropriate session names

3. **Regular Cleanup**
   - Delete sessions you no longer use
   - Keeps directory organized

4. **Dedicated Accounts**
   - Consider using specific accounts for scraping
   - Reduces risk if cookies are compromised

## Troubleshooting

### "Cookie file not found"
- File was deleted or moved
- Check the filename matches
- Re-authenticate using GUI

### "Session expired"
- Cookies have expired
- Delete old file and re-authenticate

### "Access denied" despite cookies
- Site may require 2FA again
- IP address changed
- Cookie was invalidated by site
- Re-authenticate to get fresh cookies

## Example Files

This directory might contain:
```
cookies/
├── google_personal.json
├── google_work.json
├── facebook_main.json
├── linkedin_profile.json
└── github_private_repos.json
```

---

**⚠️ Remember: Treat these files like passwords!**

**Author**: Ruslan Magana
**Website**: ruslanmv.com
