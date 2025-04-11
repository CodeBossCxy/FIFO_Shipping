async function load_shipper(){
    console.log("Successfully loaded");
    fetch('/api/get_valid_shippers',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(response => response.json()).then(data => {
        const container = document.getElementById('shipper-table-container');
        let table = '<table>';
        table += '<thead><tr><th>Shipper No</th><th>Customer Code</th></tr></thead>';
        table += '<tbody>';
        data.forEach(shipper => {
            table += `<tr shipper-url="/shipper/${shipper.Shipper_No}" style="cursor: pointer;"><td>${shipper.Shipper_No}</td><td>${shipper.Customer_Code}</td></tr>`;
        });
        table += '</tbody></table>';
        container.innerHTML = table;
    })
    .catch(error => {
        console.error('Error fetching shipper data:', error);
    });
}

load_shipper();
document.getElementById('shipper-number-input').addEventListener('keydown', function(event) {
    // console.log("Event listening ...");
    if (event.key === "Enter") {
        // console.log("Enter key pressed ...");
        send_shipper_number_input();
    }
});

async function send_shipper_number_input() {
    const shipper_number_input = document.getElementById('shipper-number-input').value;
    const res = await fetch('/api/get_shipper_containers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({shipper_number: shipper_number_input})
    }); 
    const data = await res.json();
    console.log(data);
}


