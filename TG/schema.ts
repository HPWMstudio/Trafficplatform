import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Redirects table for tracking real user visits and redirections.
 * Logs all user interactions with the landing page and tracks conversion.
 */
export const redirects = mysqlTable("redirects", {
  id: int("id").autoincrement().primaryKey(),
  visitorId: varchar("visitorId", { length: 64 }).notNull().unique(),
  targetUrl: varchar("targetUrl", { length: 512 }).notNull(),
  userAgent: text("userAgent"),
  referer: varchar("referer", { length: 512 }),
  ipAddress: varchar("ipAddress", { length: 45 }),
  deviceType: varchar("deviceType", { length: 50 }),
  country: varchar("country", { length: 2 }),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  redirected: int("redirected").default(0).notNull(), // 0 = not redirected, 1 = redirected
  redirectTime: int("redirectTime"), // Time in milliseconds before redirect
  sessionDuration: int("sessionDuration"), // Total session duration in milliseconds
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Redirect = typeof redirects.$inferSelect;
export type InsertRedirect = typeof redirects.$inferInsert;

/**
 * Redirection campaigns table for managing multiple redirection targets.
 * Allows operators to create and manage different campaigns from the C2.
 */
export const campaigns = mysqlTable("campaigns", {
  id: int("id").autoincrement().primaryKey(),
  campaignId: varchar("campaignId", { length: 64 }).notNull().unique(),
  campaignName: varchar("campaignName", { length: 255 }).notNull(),
  targetUrl: varchar("targetUrl", { length: 512 }).notNull(),
  landingPageUrl: varchar("landingPageUrl", { length: 512 }).notNull(),
  active: int("active").default(1).notNull(),
  conversionGoal: varchar("conversionGoal", { length: 255 }),
  trackingEnabled: int("trackingEnabled").default(1).notNull(),
  totalVisits: int("totalVisits").default(0).notNull(),
  totalRedirects: int("totalRedirects").default(0).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Campaign = typeof campaigns.$inferSelect;
export type InsertCampaign = typeof campaigns.$inferInsert;