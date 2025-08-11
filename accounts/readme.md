models overview (brief, by section)
CustomUserManager: only create_user/create_superuser; hashes password; no business logic.

Organization: tenant container + policy knobs (data-only). Constraints/indexes prevent dupes and speed queries.

OrganizationAccessRule: IP allow/deny CIDRs; clean() validates CIDR.

CustomUser: email login, profile fields, verification flags, basic lockout counters, MFA flags. No business logic.

Membership: user↔org link with role; constraints enforce one primary per user and one active link per org.

Invite: pending joining; uniqueness constraint prevents duplicate pending invites.

EmailVerificationToken / PasswordResetToken: short-lived tokens; actual flow in services.

RecoveryCode: hashed emergency MFA codes (future).

AuthEvent: lightweight audit trail for sign-in/out/password change
