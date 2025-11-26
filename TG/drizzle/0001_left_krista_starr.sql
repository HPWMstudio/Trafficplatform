CREATE TABLE `campaigns` (
	`id` int AUTO_INCREMENT NOT NULL,
	`campaignId` varchar(64) NOT NULL,
	`campaignName` varchar(255) NOT NULL,
	`targetUrl` varchar(512) NOT NULL,
	`landingPageUrl` varchar(512) NOT NULL,
	`active` int NOT NULL DEFAULT 1,
	`conversionGoal` varchar(255),
	`trackingEnabled` int NOT NULL DEFAULT 1,
	`totalVisits` int NOT NULL DEFAULT 0,
	`totalRedirects` int NOT NULL DEFAULT 0,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `campaigns_id` PRIMARY KEY(`id`),
	CONSTRAINT `campaigns_campaignId_unique` UNIQUE(`campaignId`)
);
--> statement-breakpoint
CREATE TABLE `redirects` (
	`id` int AUTO_INCREMENT NOT NULL,
	`visitorId` varchar(64) NOT NULL,
	`targetUrl` varchar(512) NOT NULL,
	`userAgent` text,
	`referer` varchar(512),
	`ipAddress` varchar(45),
	`deviceType` varchar(50),
	`country` varchar(2),
	`timestamp` timestamp NOT NULL DEFAULT (now()),
	`redirected` int NOT NULL DEFAULT 0,
	`redirectTime` int,
	`sessionDuration` int,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `redirects_id` PRIMARY KEY(`id`),
	CONSTRAINT `redirects_visitorId_unique` UNIQUE(`visitorId`)
);
