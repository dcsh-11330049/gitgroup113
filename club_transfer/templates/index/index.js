let clubs;
let fetchtimer; // Timer for automatic fetching

function createCell(content, className = '', nullContent='無', nullClass='none', nullClass_append = false) {
    const cell = document.createElement('td');
    cell.textContent = content || nullContent;
    if (className)
        cell.className = className;
    else if (!content && nullClass) {
        if (nullClass_append)
            cell.className += nullClass;
        else
            cell.className = nullClass;
    }
    return cell;
}

function displayClubs(clubs) {
    const table = document.getElementById('clubs-overview');
    const tbody = table.getElementsByTagName('tbody')[0];
    tbody.innerHTML = ''; // Clear existing rows

    clubs.forEach(club => {
        const row = document.createElement('tr');
        row.classList.add("club-row");
        row.appendChild(createCell(club.name));
        row.appendChild(createCell(club.president_name, '', '無社長'));
        row.appendChild(createCell(club.description_url || club.description, '', '無說明'));
        if (club.max_capacity) {
            const capacity_label = `${club.current_members} / ${club.max_capacity}`;
            // Determine capacity class (full, nearly-full, not-full)
            let capacity_class;
            if (club.current_members >= club.max_capacity)
                capacity_class = 'full';
            else if (club.current_members >= club.max_capacity * 0.7)
                capacity_class = 'nearly-full';
            else 
                capacity_class = 'not-full';

            row.appendChild(createCell(capacity_label, capacity_class));
            row.appendChild(createCell(capacity_class == "full" ? '已滿額' : club.max_capacity - club.current_members, capacity_class));
        } else {
            row.appendChild(createCell(club.current_members, 'not-full'));
            row.appendChild(createCell('無上限', 'not-full'));
        }
        tbody.appendChild(row);
    });
}

function fetchClubs() {
    fetch('/clubs/api/clubs/')
        .then(response => response.json())
        .then(fetched_clubs => {
            clubs = fetched_clubs; // Store the fetched clubs
            displayClubs(clubs);
        });
}

document.addEventListener('DOMContentLoaded', () => {
    fetchClubs();
    fetchtimer = setInterval(fetchClubs, 10000); // Refresh every 10 seconds
});