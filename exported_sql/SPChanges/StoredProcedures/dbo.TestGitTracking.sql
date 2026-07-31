-- Database: SPChanges
-- Object: dbo.TestGitTracking
-- Event: ALTER_PROCEDURE
-- Changed By: DESKTOP-5TOUO1R\Suryaanand
-- Changed At: 2026-07-31 12:51:37.587000
-- Audit ChangeId: 2
-- Auto-generated from SQL Server.

CREATE PROCEDURE dbo.TestGitTracking
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        'Version 2' AS Message,
        SYSDATETIME() AS ChangedAt;
END;
