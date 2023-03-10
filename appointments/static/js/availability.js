$(document).ready(function () {

    //UTILITY FUNCTION
    //Converts time in format "HH:mm AM/PM" to "HH:mm"
    const convertTime12to24 = (time12h) => {
        const [time, modifier] = time12h.split(' ');
        let [hours, minutes] = time.split(':');

        if (hours === '12') {
            hours = '00';
        }
        if (modifier === 'PM') {
            hours = parseInt(hours, 10) + 12;
        }

        return `${hours}:${minutes}`;
    }

    //UTILITY FUNCTION
    function addMinutes(date, minutes){
        const MILLIS_PER_MINUTE = 60000;
        return new Date(date.getTime() + minutes*MILLIS_PER_MINUTE);
    }

    //UTILITY FUNCTION
    function getTimeAMPMString(time){
        return time.toLocaleTimeString([], {hour: '2-digit',minute: '2-digit'});
    }

    $('.timepicker_1').timepicker({
        timeFormat: 'h:mm p',
        interval: 30,
        defaultTime: '9:00',
        startTime: '00:00',
        dropdown: true,
        scrollbar: true,
        dynamic: false,
        change: function(){
            validateStartEndTime();
            validateSlotDuration();
            generateAvailabilities();
            validateSelectedAvailabilities();
        }
    });

    $('.timepicker_2').timepicker({
        timeFormat: 'h:mm p',
        interval: 30,
        defaultTime: '17:00',
        startTime: '00:00',
        dropdown: true,
        scrollbar: true,
        dynamic: false,
        change: function(){
            validateStartEndTime();
            validateSlotDuration();
            generateAvailabilities();
            validateSelectedAvailabilities();
        }
    });

    $('#id_slot_duration_hours').change(function(){
        validateSlotDuration();
        generateAvailabilities();
    });

    $('#id_slot_duration_minutes').change(function(){
        validateSlotDuration();
        generateAvailabilities();
    });

    $('#id_start_date').change(function(){
        validateStartEndDate();
    });

    $('#id_end_date').change(function(){
        validateStartEndDate();
    });

    $('#availability-select').change(function(){
       validateSelectedAvailabilities();
    });

    //Ensure that start date is not after end date
    function validateStartEndDate(){
        let startDate = $('#id_start_date').val();
        let endDate = $('#id_end_date').val();
        if (startDate !== "" && endDate !== ""){
            let startDateObject = new Date(String(startDate) + ' ' + '00:00');
            let endDateObject = new Date(String(endDate) + ' ' + '00:00');

            let isValidDate = startDateObject <= endDateObject;

            if (!isValidDate){
                $('#date-error').removeClass('hidden');
            }
            else{
                $('#date-error').addClass('hidden');
            }
            return isValidDate;
        }
        return false;


    }

    //Ensure that start time is not after end time
    function validateStartEndTime() {
        let startTime = $('#start_time').val();
        let endTime = $('#end_time').val();

        let startTime24 = convertTime12to24(startTime);
        let endTime24 = convertTime12to24(endTime);

        // Need this check because endTime is not defined properly upon opening the page
        if (!String(startTime24).includes('undefined') && !String(endTime24).includes('undefined')) {
            let startTimeDate = new Date(new Date().toDateString() + ' ' + startTime24);
            let endTimeDate = new Date(new Date().toDateString() + ' ' + endTime24);

            let isValidTime = startTimeDate < endTimeDate;

            if (!isValidTime) {
                $('#time-error').removeClass('hidden');
            } else {
                $('#time-error').addClass('hidden');
            }
            return isValidTime;
        }
        return false;

    }

    //Ensure that the slot duration is not greater than the difference between the start and end times
    function validateSlotDuration() {
        //get the difference between end and start time
        //if slot duration is > than difference, error message
        let slotHours = $('#id_slot_duration_hours').val();
        let slotMinutes = $('#id_slot_duration_minutes').val();
        let slotDurationMinutes = parseInt(slotHours)*60 + parseInt(slotMinutes);

        const MILLIS_PER_MINUTE = 60000;

        if (validateStartEndTime()){
            let startTimeDate = new Date(new Date().toDateString() + ' ' + convertTime12to24($('#start_time').val()));
            let endTimeDate = new Date(new Date().toDateString() + ' ' + convertTime12to24($('#end_time').val()));

            let slotErrorElement = $('#slot-error');

            let slotTooLongMessage = "Invalid slot duration: The slot duration cannot fit in your start/end interval";
            let slotTooShortMessage = "Invalid slot duration: Cannot have a duration of 0 minutes";

            const diffTime = Math.abs(endTimeDate - startTimeDate)/MILLIS_PER_MINUTE;

            let isSlotTooLong = (slotDurationMinutes > diffTime);
            let isSlotTooShort = (slotDurationMinutes === 0);
            let isSlotInvalid = (isSlotTooLong || isSlotTooShort);

            console.log(isSlotInvalid);

            if (isSlotInvalid) {
                slotErrorElement.removeClass('hidden');

                if (isSlotTooLong) {
                    slotErrorElement.text(slotTooLongMessage)
                } else {
                    slotErrorElement.text(slotTooShortMessage)
                }
            }
            else{
                slotErrorElement.addClass('hidden');
            }
            return (!isSlotInvalid);
        }
        return false;
    }

    function generateAvailabilities(){

        if(validateStartEndTime() && validateSlotDuration()){
            let startTimeDate = new Date(new Date().toDateString() + ' ' + convertTime12to24($('#start_time').val()));
            let endTimeDate = new Date(new Date().toDateString() + ' ' + convertTime12to24($('#end_time').val()));
            let slotDurationMinutes = parseInt($('#id_slot_duration_hours').val())*60 + parseInt($('#id_slot_duration_minutes').val());

            let currentTime = startTimeDate;
            let endTime = null;

            let availabilities = [];
            while (currentTime < endTimeDate) {
                //If the time difference between start and end does not give a remainder of 0,
                //for the last availability round the time. The last availability won't have the same slot duration as
                //the others.
                if (addMinutes(currentTime, slotDurationMinutes) > endTimeDate) {
                    endTime = endTimeDate;
                    //Create json to be used in backend
                    let timeData = {
                        start: currentTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', hour12: false}),
                        end: endTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', hour12: false})
                    };
                    availabilities.push({
                        text: getTimeAMPMString(currentTime) + ' ' + getTimeAMPMString(endTime),
                        data: timeData
                    });
                    //Exit loop because end time has been reached
                    break;
                }
                //Get the end time of the availability by adding the slot duration
                endTime = addMinutes(currentTime, slotDurationMinutes);
                //Create json to be used in backend
                let timeData = {
                    start: currentTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', hour12: false}),
                    end: endTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', hour12: false})
                };
                availabilities.push({
                    text: getTimeAMPMString(currentTime) + '-' + getTimeAMPMString(endTime),
                    data: timeData
                });
                //increment to next availability
                currentTime = endTime;
            }

            //Reset all the previously generated availabilities
            $('.availability-select2').empty();

            $.each(availabilities, function (i, item) {
                $('.availability-select2').append($('<option>', {
                    name: 'availability_select',
                    value: JSON.stringify(item.data),
                    text: item.text,
                    selected: 'selected'
                }));
            });

        }
    }

    //Ensure the selected availabilities field is not blank
    function validateSelectedAvailabilities(){
        let availabilities_selected = $('#availability-select').val();
        if (!availabilities_selected) {
            $('#availability_error').removeClass('hidden');
        }
        else{
            $('#availability_error').addClass('hidden');
        }
        return availabilities_selected;
    }
    //Validate all fields before sending post request
    function validateForm(event) {
        let valid = validateStartEndDate() && validateStartEndTime() && validateSlotDuration() && validateSelectedAvailabilities();
        if(!valid){
            event.preventDefault();
        }
    }

    $('#availability-form').submit(function(event){
        validateForm(event)
    });

    $('.availability-select2').select2({
        placeholder: 'Please select availabilities for patients to book appointments'
    });
});

//jQuery for week day selection
$(document).on('click','.select-multi-days',function(){

            if($(this).attr('data-action') == 'select_all_days'){
                $('input.days_checkbox').prop('checked','checked')
                $(this).addClass('hidden')
                $(".deselect").removeClass('hidden')
            }
            if($(this).attr('data-action') == 'deselect_all_days'){
                $('input.days_checkbox').prop('checked',false)
                $('.selecta-all').removeClass('hidden')
                $(this).addClass('hidden')
            }
            if($(this).attr('data-action') == 'select_weekdays'){
                $('input.days_checkbox').each(function(){
                    if($(this).closest('label').text().trim() != "Saturday" && $(this).closest('label').text().trim() != "Sunday"){
                        $(this).prop('checked','checked')
                    }
                })
                $('.selecta-all').addClass('hidden')
                $('.deselect').removeClass('hidden')
            }

            if($(this).attr('data-action') == 'select_weekends'){
                $('input.days_checkbox').each(function(){
                    if($(this).closest('label').text().trim() == "Saturday" || $(this).closest('label').text().trim() == "Sunday"){
                        $(this).prop('checked','checked')
                    }
                })
                $('.selecta-all').addClass('hidden')
                $('.deselect').removeClass('hidden')
            }
        })