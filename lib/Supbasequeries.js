import { createClient } from '@supabase/supabase-js'

// Initialize the Supabase client using public environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

/**
 * 1. Fetch Vital Signs & Health Logs for a Specific Astronaut
 * Orders by measured_at descending (newest telemetry first)
 */
export async function getAstronautVitals(astronautId) {
    const { data, error } = await supabase
        .from('health_logs')
        .select('*')
        .eq('astronaut_id', astronautId)
        .order('measured_at', { ascending: false })
        .limit(50)

    if (error) {
        console.error('Error fetching health logs:', error.message)
        return []
    }
    return data
}

/**
 * 2. Fetch Personal Radiation Dose Records
 * Implements Section 4.1 original_value and original_unit standards
 */
export async function getPersonalDoses(astronautId) {
    const { data, error } = await supabase
        .from('personal_dose_records')
        .select('*')
        .eq('astronaut_id', astronautId)
        .order('measured_at', { ascending: false })

    if (error) {
        console.error('Error fetching radiation dose records:', error.message)
        return []
    }
    return data
}

/**
 * 3. Fetch Environmental Readings for Habitat Monitoring
 */
export async function getEnvironmentalReadings(missionId) {
    const { data, error } = await supabase
        .from('environmental_readings')
        .select('*')
        .eq('mission_id', missionId)
        .order('measured_at', { ascending: false })
        .limit(100)

    if (error) {
        console.error('Error fetching environmental readings:', error.message)
        return []
    }
    return data
}

/**
 * 4. Fetch Active Health Alerts for Crew or Location
 */
export async function getActiveAlerts() {
    const { data, error } = await supabase
        .from('health_alerts')
        .select(`
            *,
            alert_rules (rule_name, severity_level, description)
        `)
        .eq('resolved', false)
        .order('created_at', { ascending: false })

    if (error) {
        console.error('Error fetching active alerts:', error.message)
        return []
    }
    return data
}


//NARA ANG SHIT PARA MA FETCH

import { getAstronautVitals } from '@/lib/supabaseQueries'

export default async function AstronautDashboard({ params }) {
    const vitals = await getAstronautVitals(params.astronautId)

    return (
        <div>
            <h2>Live Telemetry Stream</h2>
            {/* Render vitals chart or cards */}
        </div>
    )
}