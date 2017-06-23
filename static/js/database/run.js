$(document).ready(function() {
	function build() {
		var data = {};
		data['repeat'] = $("input[name='regular']:checked").val();
		data['mode'] = $("input[name='result-process']:checked").val();
		data['data'] = {}
		if(data['repeat'] == 'once') {
			data['data']['date'] = $("input[name='date-input']").val(); 
			data['data']['time'] = $("input[name='time-input']").val();
		}
		if(data['repeat'] == 'everyday') {
			data['data']['time'] = $("input[name='time-input']").val();
		}
		if(data['repeat'] == 'custom') {
			$(".week-wrap").each(function() {
				if(!$(this).hasClass('active')) 
					return;
				data['data'][$(this).attr('itemprop').trim()] = $(this).find("input").val()
			}); 
		}

		return data;
	}

	$(".date-input").hide();
	$(".time-input").hide();
	$(".custom-radio").click(function() {
		$(this).siblings().removeClass('active');
		$(this).addClass('active');
		if(!$(this).parent().hasClass("schedule-options"))
			return; 

		if(this.innerText != 'Custom') {
			$(".weekday").addClass('disabled');
			$(".week-wrap input").attr('disabled', true)
		} else {
			$(".weekday").removeClass('disabled');
			$(".week-wrap input").attr('disabled', false)
			$(".date-input").hide();
			$(".time-input").hide();
		}
		if(this.innerText == 'Everyday') {
			$(".date-input").hide();
			$(".time-input").show();
		}
		if(this.innerText == 'Once') {
			$(".date-input").show();
			$(".time-input").show();
		}
	}); 
	$(".weekday").click(function() {
		$(this).toggleClass('btn-primary');
		$(this).parent().toggleClass('active');
		var radio = $(".schedule-options .custom-radio");
		radio[radio.length-1].click();
	}); 
	$("#save-run-configuration").click(function() {
		var data = build();
		$.post(
			url, {
				data: JSON.stringify(data), 
				csrfmiddlewaretoken: csrf
			}, function(r) {
				console.log(r);
			} ); 
	}); 

	console.log($("input[name='regular']").val());

	$("input[value='"+interval['repeat']+"']").parent().click();
	$("input[value='"+interval['mode']+"'").parent().click();

	if($("input[name='regular']:checked").val() == 'everyday') {
		$("input[name='time-input']").val(interval['data']['time']);
	}
	if($("input[name='regular']:checked").val() == 'once') {
		$("input[name='date-input']").val(interval['data']['date']);
		$("input[name='time-input']").val(interval['data']['time']);
	}
	if($("input[name='regular']:checked").val() == 'custom') {
		for(item in interval['data']) {
			$(".week-wrap[itemprop='"+item+"'] > div").click();
			$(".week-wrap[itemprop='"+item+"'] > input").val(interval['data'][item])
			console.log(item);
		}
	}	

}); 
