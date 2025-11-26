import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, redirects, campaigns, InsertRedirect, InsertCampaign } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

/**
 * Get or create a redirect record for a visitor.
 */
export async function logRedirect(data: InsertRedirect) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot log redirect: database not available");
    return undefined;
  }

  try {
    const result = await db.insert(redirects).values(data);
    return result;
  } catch (error) {
    console.error("[Database] Failed to log redirect:", error);
    throw error;
  }
}

/**
 * Update a redirect record (e.g., mark as redirected).
 */
export async function updateRedirect(visitorId: string, updates: Partial<InsertRedirect>) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot update redirect: database not available");
    return undefined;
  }

  try {
    const result = await db
      .update(redirects)
      .set(updates)
      .where(eq(redirects.visitorId, visitorId));
    return result;
  } catch (error) {
    console.error("[Database] Failed to update redirect:", error);
    throw error;
  }
}

/**
 * Get campaign statistics.
 */
export async function getCampaignStats(campaignId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get campaign stats: database not available");
    return undefined;
  }

  try {
    const campaign = await db
      .select()
      .from(campaigns)
      .where(eq(campaigns.campaignId, campaignId))
      .limit(1);

    if (campaign.length === 0) return null;

    return campaign[0];
  } catch (error) {
    console.error("[Database] Failed to get campaign stats:", error);
    throw error;
  }
}

/**
 * Create or update a campaign.
 */
export async function upsertCampaign(data: InsertCampaign) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert campaign: database not available");
    return undefined;
  }

  try {
    const result = await db
      .insert(campaigns)
      .values(data)
      .onDuplicateKeyUpdate({
        set: {
          targetUrl: data.targetUrl,
          landingPageUrl: data.landingPageUrl,
          active: data.active,
          updatedAt: new Date(),
        },
      });
    return result;
  } catch (error) {
    console.error("[Database] Failed to upsert campaign:", error);
    throw error;
  }
}

// TODO: add feature queries here as your schema grows.
