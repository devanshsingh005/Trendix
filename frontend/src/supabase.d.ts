declare module '@supabase/supabase-js' {
    interface PostgrestError {
        message: string;
        details: string;
        hint: string;
        code: string;
    }

    interface PostgrestResponse<T> {
        data: T[] | null;
        error: PostgrestError | null;
        count: number | null;
        status: number;
        statusText: string;
    }

    interface PostgrestFilterBuilder<T> {
        select(columns?: string): PostgrestFilterBuilder<T>;
        in(column: string, values: any[]): PostgrestFilterBuilder<T>;
        eq(column: string, value: any): PostgrestFilterBuilder<T>;
        neq(column: string, value: any): PostgrestFilterBuilder<T>;
        gt(column: string, value: any): PostgrestFilterBuilder<T>;
        gte(column: string, value: any): PostgrestFilterBuilder<T>;
        lt(column: string, value: any): PostgrestFilterBuilder<T>;
        lte(column: string, value: any): PostgrestFilterBuilder<T>;
        like(column: string, pattern: string): PostgrestFilterBuilder<T>;
        ilike(column: string, pattern: string): PostgrestFilterBuilder<T>;
        is(column: string, value: any): PostgrestFilterBuilder<T>;
        contains(column: string, value: any): PostgrestFilterBuilder<T>;
        containedBy(column: string, value: any): PostgrestFilterBuilder<T>;
        range(column: string, range: [any, any]): PostgrestFilterBuilder<T>;
        overlaps(column: string, range: [any, any]): PostgrestFilterBuilder<T>;
        order(column: string, options?: { ascending?: boolean }): PostgrestFilterBuilder<T>;
        limit(count: number): PostgrestFilterBuilder<T>;
        then(): Promise<PostgrestResponse<T>>;
    }

    export interface SupabaseClient {
        from<T = any>(table: string): PostgrestFilterBuilder<T>;
    }

    export function createClient(url: string, key: string): SupabaseClient;
}
