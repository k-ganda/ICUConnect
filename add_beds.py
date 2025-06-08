from app import create_app, db
from app.models import Hospital, Bed

app = create_app()

bed_counts = {
    2: 15,
    3: 6,
    5: 0,
    6: 4,
    7: 11,
}

with app.app_context():
    for hospital_id, total_beds in bed_counts.items():
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            print(f"❌ Hospital with ID {hospital_id} not found.")
            continue

        existing_beds = Bed.query.filter_by(hospital_id=hospital_id).count()
        if existing_beds > 0:
            print(f"⚠️ Hospital '{hospital.name}' already has {existing_beds} beds. Skipping...")
            continue

        for i in range(1, total_beds + 1):
            bed = Bed(
                hospital_id=hospital_id,
                bed_number=i,
                is_occupied=False,
                bed_type='ICU'
            )
            db.session.add(bed)

        print(f"✅ Added {total_beds} ICU beds for hospital '{hospital.name}'.")

    db.session.commit()
    print("✅✅ All bed records successfully committed.")
