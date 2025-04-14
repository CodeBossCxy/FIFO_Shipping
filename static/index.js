async function load_shipper(){
    console.log("Successfully loaded");
    fetch('/',
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
            table += `<tr onclick="window.location.href='/shipper/${shipper.Shipper_No}'" style="cursor: pointer;"><td>${shipper.Shipper_No}</td><td>${shipper.Customer_Code}</td></tr>`;
        });
        table += '</tbody></table>';
        container.innerHTML = table;
    })
    .catch(error => {
        console.error('Error fetching shipper data:', error);
    });
}


async function send_shipper_number_input() {
    const shipper_number_input = document.getElementById('shipper-number-input');
    // const shipper_number_form = document.getElementById('shipper-number-form');


    shipper_number_input.addEventListener('keydown', function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            console.log("shipper_number_input: ", shipper_number_input.value);
            // shipper_number_form.submit();
            window.location.href = `/shipper/${encodeURIComponent(shipper_number_input.value)}`;
        }
    });
}


load_shipper();
send_shipper_number_input();
