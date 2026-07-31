-- Database: SPChanges
-- Object: dbo.TestGitTracking
-- Latest Event: ALTER_PROCEDURE
-- Changed By: DESKTOP-5TOUO1R\Suryaanand
-- Changed At: 2026-07-31 13:02:59.337000
-- Audit Change IDs: 3
-- Auto-generated from SQL Server.

CREATE PROCEDURE dbo.TestGitTracking
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        'Version 3' AS Message,
        SYSDATETIME() AS ChangedAt,
        ORIGINAL_LOGIN() AS ModifiedBy;
END;
