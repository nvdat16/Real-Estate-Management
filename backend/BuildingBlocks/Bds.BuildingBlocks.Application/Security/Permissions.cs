namespace Bds.BuildingBlocks.Application.Security;

public static class Permissions
{
    public const string UsersManage = "users.manage";
    public const string ProjectsManage = "projects.manage";
    public const string ListingsCreate = "listings.create";
    public const string ListingsApprove = "listings.approve";
    public const string KycSubmit = "kyc.submit";
    public const string KycReview = "kyc.review";
    public const string ContractsCreate = "contracts.create";
    public const string ContractsSign = "contracts.sign";
    public const string InvoicesManage = "invoices.manage";
    public const string CommissionsManage = "commissions.manage";
    public const string CommissionsReadOwn = "commissions.read_own";
    public const string ReportsRead = "reports.read";
    public const string AuditLogsRead = "audit_logs.read";
}