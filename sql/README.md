# 📁 Supabase SQL Scripts

This folder contains SQL scripts to manage the Supabase database.

## 📋 Available Files

### `create_complete_database.sql`
**Main script** - Creates the entire database in one go.
- Drops existing tables (if they exist)
- Creates all tables with their constraints
- Creates all indexes
- Creates all sequences

**When to use:**
- First installation
- Complete database reset
- After modifying table structure

### `cleanup_supabase.sql`
**Cleanup script** - Deletes all data except orders.
- Deletes: sessions, messages, tickets, summaries, feedback
- **Keeps**: orders
- Resets sequences

**When to use:**
- To test with an empty database
- To start fresh without losing test orders

### `insert_test_orders.sql`
**Insert test orders** - Adds 5 test orders to the database.
- Inserts orders: 12345, 67890, 11111, 22222, 10262006
- Uses `ON CONFLICT` to update if orders already exist
- No manual typing needed!

**When to use:**
- To add test orders quickly
- After cleaning the database
- When you need test data for development

## 🚀 Usage

1. Go to Supabase **SQL Editor**
2. Copy the content of the script you want to execute
3. Run it

## ⚠️ Warning

- `create_complete_database.sql` deletes **ALL** existing tables
- `cleanup_supabase.sql` deletes **ALL** data except orders
- Make a backup before running these scripts in production
