USE [INV_DEV_LAND]
GO
/****** Object:  Trigger [dbo].[TRG_PROSPECT_STATUS_AUDIT]    Script Date: 12/17/2019 3:21:00 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER TRIGGER [dbo].[TRG_PROSPECT_STATUS_AUDIT]
	ON [dbo].[DEV_PROSPECTS]
	AFTER INSERT, UPDATE
	NOT FOR REPLICATION
AS
IF ( UPDATE ([STATUS]) )  
	BEGIN 
		IF EXISTS ( SELECT 1 FROM Inserted WHERE [STATUS] in (5, 7) )
			BEGIN
				IF EXISTS ( SELECT 1 FROM Deleted )
					BEGIN
						-- updated
						INSERT INTO [DBO].[DEV_PROSPECT_STATUS_UPDATE_LOG] (
							[INV_DEV_PROSPECT_ID],	[INV_DEV_PROJECT_ID]
							, [PROJECT_NAME], [PROJECT_STATUS], [DEVELOPER]
							, [APN], [APN2]
							, [LAND_AGENCY_1], [LAND_AGENT_1], [LAND_AGENCY_2], [LAND_AGENT_2]
							, [OLD_STATUS], [NEW_STATUS]
							, [last_edited_user], [last_edited_date]
						) 
						SELECT i.[INV_DEV_PROSPECT_ID], i.[INV_DEV_PROJECT_ID]
							, p.[PROJECT_NAME], ps.[TEXT_EN], p.[DEVELOPER]
							, i.[APN], i.[APN2]
							, i.[LAND_AGENCY_1], i.[LAND_AGENT_1], i.[LAND_AGENCY_2], i.[LAND_AGENT_2]
							, rs1.[TEXT_EN], rs2.[TEXT_EN]
							, i.[last_edited_user], i.[last_edited_date]
						FROM Inserted i 
							join Deleted d 
								on  d.[INV_DEV_PROSPECT_ID] = i.[INV_DEV_PROSPECT_ID]
									and d.[INV_DEV_PROJECT_ID] = i.[INV_DEV_PROJECT_ID]
									and (d.[STATUS] <> i.[STATUS] or d.[STATUS] is null)
							join [DBO].[DEV_PROJECTS] p
								on p.[INV_DEV_PROJECT_ID] = i.[INV_DEV_PROJECT_ID]
							join [DBO].DOM_DEV_PROJECT_STATUS ps 
								on ps.[CODED_VALUE] = p.[STATUS]
							left outer join [DBO].[DOM_DEV_PROSPECT_STATUS] rs1 
								on rs1.[CODED_VALUE] = d.[STATUS]
							join [DBO].[DOM_DEV_PROSPECT_STATUS] rs2 
								on rs2.[CODED_VALUE] = i.[STATUS]					
						WHERE i.[STATUS] in (5, 7) 
					END
				ELSE
					BEGIN
						-- inserted
						INSERT INTO [DBO].[DEV_PROSPECT_STATUS_UPDATE_LOG] (
							[INV_DEV_PROSPECT_ID],	[INV_DEV_PROJECT_ID]
							, [PROJECT_NAME], [PROJECT_STATUS], [DEVELOPER]
							, [APN], [APN2]
							, [LAND_AGENCY_1], [LAND_AGENT_1], [LAND_AGENCY_2], [LAND_AGENT_2]
							, [OLD_STATUS], [NEW_STATUS]
							, [last_edited_user], [last_edited_date]
						) 
						SELECT i.[INV_DEV_PROSPECT_ID], i.[INV_DEV_PROJECT_ID]
							, p.[PROJECT_NAME], ps.[TEXT_EN], p.[DEVELOPER]
							, i.[APN], i.[APN2]
							, i.[LAND_AGENCY_1], i.[LAND_AGENT_1], i.[LAND_AGENCY_2], i.[LAND_AGENT_2]
							, NULL, rs2.[TEXT_EN]
							, i.[created_date], i.[created_date]
						FROM Inserted i 
							join [DBO].[DEV_PROJECTS] p
								on p.[INV_DEV_PROJECT_ID] = i.[INV_DEV_PROJECT_ID]
							join [DBO].DOM_DEV_PROJECT_STATUS ps 
								on ps.[CODED_VALUE] = p.[STATUS]
							join [DBO].[DOM_DEV_PROSPECT_STATUS] rs2 
								on rs2.[CODED_VALUE] = i.[STATUS]					
						WHERE i.[STATUS] in (5, 7) 				
					END
			END
	END
